import os
from fastapi import FastAPI, Request, Form, Query
from fastapi.responses import HTMLResponse, RedirectResponse
from fastapi.templating import Jinja2Templates
from starlette.middleware.sessions import SessionMiddleware
from passlib.context import CryptContext
import psycopg


# =========================
# App setup
# =========================

app = FastAPI(title="Shop System", version="0.1.0")
templates = Jinja2Templates(directory="app/templates")

app.add_middleware(
    SessionMiddleware,
    secret_key=os.environ.get("SESSION_SECRET", "dev-only-change-me"),
    session_cookie=os.environ.get("SESSION_COOKIE_NAME", "shop_session"),
    same_site="lax",
    https_only=os.environ.get("SESSION_HTTPS_ONLY", "false").lower() == "true",
)


@app.middleware("http")
async def honor_forwarded_path_prefix(request: Request, call_next):
    """Run correctly below an Nginx path such as /berhea1 or /shop."""
    prefix = request.headers.get("x-forwarded-prefix", "").strip().rstrip("/")
    if prefix and prefix.startswith("/"):
        request.scope["root_path"] = prefix

    response = await call_next(request)
    location = response.headers.get("location")
    if prefix and location and location.startswith("/") and not location.startswith(f"{prefix}/"):
        response.headers["location"] = f"{prefix}{location}"
    return response

pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

DATABASE_URL = os.environ.get("DATABASE_URL")
if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not set. Add it to .env and ensure compose uses env_file: .env")


def db():
    return psycopg.connect(DATABASE_URL)


def admin_required(request: Request):
    """Redirect to login if not logged in as admin."""
    if request.session.get("admin_user_role") != "admin":
        return RedirectResponse("/admin/login", status_code=303)
    return None


# =========================
# Public pages
# =========================

@app.get("/", response_class=HTMLResponse)
def home(request: Request):
    return templates.TemplateResponse("home.html", {"request": request})


@app.post("/check", response_class=HTMLResponse)
def check_access_page(request: Request, barcode: str = Form(...)):
    barcode = barcode.strip()
    if not barcode:
        return RedirectResponse("/", status_code=303)

    with db() as conn:
        with conn.cursor() as cur:
            # Find user by barcode_value
            cur.execute(
                "SELECT id, full_name, barcode_value, is_active FROM users WHERE barcode_value=%s",
                (barcode,),
            )
            row = cur.fetchone()

            if not row:
                return templates.TemplateResponse(
                    "student.html",
                    {
                        "request": request,
                        "user": {"full_name": "Unknown User", "barcode_value": barcode},
                        "allowed_machines": [],
                        "blocked_machines": [],
                    },
                )

            user_id, full_name, barcode_value, is_active = row

            if not is_active:
                return templates.TemplateResponse(
                    "student.html",
                    {
                        "request": request,
                        "user": {"full_name": f"{full_name} (INACTIVE)", "barcode_value": barcode_value},
                        "allowed_machines": [],
                        "blocked_machines": [],
                    },
                )

            # User's valid certs (not expired)
            cur.execute(
                """
                SELECT c.id, c.code
                FROM user_certifications uc
                JOIN certifications c ON c.id = uc.certification_id
                WHERE uc.user_id = %s
                  AND (uc.expires_at IS NULL OR uc.expires_at > NOW())
                """,
                (user_id,),
            )
            user_cert_ids = {cid for (cid, _) in cur.fetchall()}

            # Load active machines
            cur.execute(
                """
                SELECT id, name, kiosk_id, location
                FROM machines
                WHERE status = 'active'
                ORDER BY name
                """
            )
            machines = cur.fetchall()

            allowed = []
            blocked = []

            for mid, name, kiosk_id, location in machines:
                cur.execute(
                    """
                    SELECT c.id, c.code
                    FROM machine_requirements mr
                    JOIN certifications c ON c.id = mr.certification_id
                    WHERE mr.machine_id = %s
                    """,
                    (mid,),
                )
                req = cur.fetchall()
                req_ids = {cid for (cid, _) in req}

                missing_ids = req_ids - user_cert_ids
                missing_codes = [code for (cid, code) in req if cid in missing_ids]

                machine_obj = {"id": mid, "name": name, "kiosk_id": kiosk_id, "location": location}

                if not missing_ids:
                    allowed.append(machine_obj)
                else:
                    blocked.append({"machine": machine_obj, "missing": missing_codes})

            return templates.TemplateResponse(
                "student.html",
                {
                    "request": request,
                    "user": {"full_name": full_name, "barcode_value": barcode_value},
                    "allowed_machines": allowed,
                    "blocked_machines": blocked,
                },
            )


# =========================
# Admin authentication (real)
# Requires admin_accounts.user_id -> users.id and users.role='admin'
# =========================

@app.get("/admin/login", response_class=HTMLResponse)
def admin_login_page(request: Request):
    return templates.TemplateResponse("admin_login.html", {"request": request, "error": None})


@app.post("/admin/login")
def admin_login(request: Request, username: str = Form(...), password: str = Form(...)):
    username = username.strip()

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                SELECT a.password_hash, a.is_active, u.role, u.full_name
                FROM admin_accounts a
                LEFT JOIN users u ON u.id = a.user_id
                WHERE a.username=%s
                """,
                (username,),
            )
            row = cur.fetchone()

            if not row:
                return templates.TemplateResponse(
                    "admin_login.html",
                    {"request": request, "error": "Invalid username or password"},
                    status_code=401,
                )

            password_hash, is_active, role, full_name = row

            if (not is_active) or (not pwd_context.verify(password, password_hash)):
                return templates.TemplateResponse(
                    "admin_login.html",
                    {"request": request, "error": "Invalid username or password"},
                    status_code=401,
                )

            if role != "admin":
                return templates.TemplateResponse(
                    "admin_login.html",
                    {"request": request, "error": "Account not linked to an admin user record."},
                    status_code=403,
                )

    request.session["admin_username"] = username
    request.session["admin_user_role"] = role
    request.session["admin_full_name"] = full_name

    return RedirectResponse("/admin", status_code=303)


@app.post("/admin/logout")
def admin_logout(request: Request):
    request.session.clear()
    return RedirectResponse("/", status_code=303)


@app.get("/admin", response_class=HTMLResponse)
def admin_dashboard(request: Request):
    redir = admin_required(request)
    if redir:
        return redir

    username = request.session.get("admin_username", "")
    admin_name = request.session.get("admin_full_name") or username

    return templates.TemplateResponse(
        "admin_dashboard.html",
        {"request": request, "admin_name": admin_name},
    )


# =========================
# Admin: Students
# =========================

@app.get("/admin/students", response_class=HTMLResponse)
def admin_students(request: Request, q: str | None = Query(default=None)):
    redir = admin_required(request)
    if redir:
        return redir

    q = (q or "").strip()

    with db() as conn:
        with conn.cursor() as cur:
            if q:
                cur.execute(
                    """
                    SELECT id, full_name, barcode_value, is_active
                    FROM users
                    WHERE role IN ('student','worker')
                      AND (barcode_value ILIKE %s OR full_name ILIKE %s)
                    ORDER BY full_name
                    LIMIT 100
                    """,
                    (f"%{q}%", f"%{q}%"),
                )
            else:
                cur.execute(
                    """
                    SELECT id, full_name, barcode_value, is_active
                    FROM users
                    WHERE role IN ('student','worker')
                    ORDER BY created_at DESC
                    LIMIT 50
                    """
                )
            students = [
                {"id": r[0], "full_name": r[1], "barcode_value": r[2], "is_active": r[3]}
                for r in cur.fetchall()
            ]

    return templates.TemplateResponse(
        "admin_students.html",
        {"request": request, "students": students, "q": q, "create_error": None},
    )


@app.post("/admin/students/create")
def admin_students_create(request: Request, full_name: str = Form(...), barcode_value: str = Form(...)):
    redir = admin_required(request)
    if redir:
        return redir

    full_name = full_name.strip()
    barcode_value = barcode_value.strip()

    try:
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO users (role, full_name, barcode_value, is_active)
                    VALUES ('student', %s, %s, TRUE)
                    """,
                    (full_name, barcode_value),
                )
            conn.commit()
        return RedirectResponse("/admin/students", status_code=303)

    except Exception as e:
        # re-render page with error
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT id, full_name, barcode_value, is_active
                    FROM users
                    WHERE role IN ('student','worker')
                    ORDER BY created_at DESC
                    LIMIT 50
                    """
                )
                students = [
                    {"id": r[0], "full_name": r[1], "barcode_value": r[2], "is_active": r[3]}
                    for r in cur.fetchall()
                ]

        return templates.TemplateResponse(
            "admin_students.html",
            {"request": request, "students": students, "q": "", "create_error": str(e)},
            status_code=400,
        )


@app.get("/admin/students/{student_id}", response_class=HTMLResponse)
def admin_student_edit(request: Request, student_id: int):
    redir = admin_required(request)
    if redir:
        return redir

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "SELECT id, full_name, barcode_value, is_active FROM users WHERE id=%s",
                (student_id,),
            )
            row = cur.fetchone()
            if not row:
                return RedirectResponse("/admin/students", status_code=303)

            student = {"id": row[0], "full_name": row[1], "barcode_value": row[2], "is_active": row[3]}

            cur.execute(
                """
                SELECT c.id, c.code, c.title
                FROM user_certifications uc
                JOIN certifications c ON c.id = uc.certification_id
                WHERE uc.user_id=%s
                  AND (uc.expires_at IS NULL OR uc.expires_at > NOW())
                ORDER BY c.code
                """,
                (student_id,),
            )
            granted = [{"id": r[0], "code": r[1], "title": r[2]} for r in cur.fetchall()]

            cur.execute("SELECT id, code, title FROM certifications ORDER BY code")
            all_certs = [{"id": r[0], "code": r[1], "title": r[2]} for r in cur.fetchall()]

    return templates.TemplateResponse(
        "admin_student_edit.html",
        {
            "request": request,
            "student": student,
            "granted": granted,
            "all_certs": all_certs,
            "save_error": None,
            "cert_error": None,
        },
    )


@app.post("/admin/students/{student_id}/update")
def admin_student_update(
    request: Request,
    student_id: int,
    full_name: str = Form(...),
    barcode_value: str = Form(...),
    is_active: str = Form(...),
):
    redir = admin_required(request)
    if redir:
        return redir

    full_name = full_name.strip()
    barcode_value = barcode_value.strip()
    active_bool = True if is_active.lower() == "true" else False

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE users
                SET full_name=%s, barcode_value=%s, is_active=%s, updated_at=NOW()
                WHERE id=%s
                """,
                (full_name, barcode_value, active_bool, student_id),
            )
        conn.commit()

    return RedirectResponse(f"/admin/students/{student_id}", status_code=303)


@app.post("/admin/students/{student_id}/certs/grant")
def admin_student_grant_cert(request: Request, student_id: int, cert_id: int = Form(...)):
    redir = admin_required(request)
    if redir:
        return redir

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO user_certifications (user_id, certification_id, granted_by)
                VALUES (%s, %s, NULL)
                ON CONFLICT (user_id, certification_id) DO NOTHING
                """,
                (student_id, cert_id),
            )
        conn.commit()

    return RedirectResponse(f"/admin/students/{student_id}", status_code=303)


@app.post("/admin/students/{student_id}/certs/revoke")
def admin_student_revoke_cert(request: Request, student_id: int, cert_id: int = Form(...)):
    redir = admin_required(request)
    if redir:
        return redir

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM user_certifications WHERE user_id=%s AND certification_id=%s",
                (student_id, cert_id),
            )
        conn.commit()

    return RedirectResponse(f"/admin/students/{student_id}", status_code=303)


@app.post("/admin/students/{student_id}/delete")
def admin_student_delete(request: Request, student_id: int):
    redir = admin_required(request)
    if redir:
        return redir

    with db() as conn:
        with conn.cursor() as cur:
            # Optional safety: prevent deleting admin accounts via this page
            cur.execute("SELECT role FROM users WHERE id=%s", (student_id,))
            row = cur.fetchone()
            if not row:
                return RedirectResponse("/admin/students", status_code=303)

            role = row[0]
            if role == "admin":
                # Don’t let student delete page remove admins
                return RedirectResponse(f"/admin/students/{student_id}", status_code=303)

            # This will cascade-delete user_certifications due to ON DELETE CASCADE
            cur.execute("DELETE FROM users WHERE id=%s", (student_id,))
        conn.commit()

    return RedirectResponse("/admin/students", status_code=303)
@app.get("/admin/certs", response_class=HTMLResponse)
def admin_certs(request: Request):
    redir = admin_required(request)
    if redir:
        return redir

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, code, title, description FROM certifications ORDER BY code")
            certs = [
                {"id": r[0], "code": r[1], "title": r[2], "description": r[3]}
                for r in cur.fetchall()
            ]

    return templates.TemplateResponse(
        "admin_certs.html",
        {"request": request, "certs": certs, "error": None},
    )


@app.post("/admin/certs/create")
def admin_certs_create(
    request: Request,
    code: str = Form(...),
    title: str = Form(...),
    description: str = Form(""),
):
    redir = admin_required(request)
    if redir:
        return redir

    code = code.strip()
    title = title.strip()
    description = (description or "").strip() or None

    try:
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO certifications (code, title, description)
                    VALUES (%s, %s, %s)
                    """,
                    (code, title, description),
                )
            conn.commit()
        return RedirectResponse("/admin/certs", status_code=303)

    except Exception as e:
        # re-render list with error
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, code, title, description FROM certifications ORDER BY code")
                certs = [
                    {"id": r[0], "code": r[1], "title": r[2], "description": r[3]}
                    for r in cur.fetchall()
                ]
        return templates.TemplateResponse(
            "admin_certs.html",
            {"request": request, "certs": certs, "error": str(e)},
            status_code=400,
        )
@app.get("/admin/machines", response_class=HTMLResponse)
def admin_machines(request: Request):
    redir = admin_required(request)
    if redir:
        return redir

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, kiosk_id, location, status FROM machines ORDER BY name")
            machines = [
                {"id": r[0], "name": r[1], "kiosk_id": r[2], "location": r[3], "status": r[4]}
                for r in cur.fetchall()
            ]

    return templates.TemplateResponse(
        "admin_machines.html",
        {"request": request, "machines": machines, "error": None},
    )


@app.post("/admin/machines/create")
def admin_machines_create(request: Request, name: str = Form(...), kiosk_id: str = Form(...), location: str = Form("")):
    redir = admin_required(request)
    if redir:
        return redir

    name = name.strip()
    kiosk_id = kiosk_id.strip()
    location = (location or "").strip() or None

    try:
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO machines (name, kiosk_id, location)
                    VALUES (%s, %s, %s)
                    """,
                    (name, kiosk_id, location),
                )
            conn.commit()
        return RedirectResponse("/admin/machines", status_code=303)

    except Exception as e:
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, kiosk_id, location, status FROM machines ORDER BY name")
                machines = [
                    {"id": r[0], "name": r[1], "kiosk_id": r[2], "location": r[3], "status": r[4]}
                    for r in cur.fetchall()
                ]
        return templates.TemplateResponse(
            "admin_machines.html",
            {"request": request, "machines": machines, "error": str(e)},
            status_code=400,
        )


@app.get("/admin/machines/{machine_id}", response_class=HTMLResponse)
def admin_machine_edit(request: Request, machine_id: int):
    redir = admin_required(request)
    if redir:
        return redir

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, kiosk_id, location, status FROM machines WHERE id=%s", (machine_id,))
            row = cur.fetchone()
            if not row:
                return RedirectResponse("/admin/machines", status_code=303)

            machine = {"id": row[0], "name": row[1], "kiosk_id": row[2], "location": row[3], "status": row[4]}

            cur.execute(
                """
                SELECT c.id, c.code, c.title
                FROM machine_requirements mr
                JOIN certifications c ON c.id = mr.certification_id
                WHERE mr.machine_id=%s
                ORDER BY c.code
                """,
                (machine_id,),
            )
            required = [{"id": r[0], "code": r[1], "title": r[2]} for r in cur.fetchall()]

            cur.execute("SELECT id, code, title FROM certifications ORDER BY code")
            all_certs = [{"id": r[0], "code": r[1], "title": r[2]} for r in cur.fetchall()]

    return templates.TemplateResponse(
        "admin_machine_edit.html",
        {"request": request, "machine": machine, "required": required, "all_certs": all_certs, "error": None},
    )


@app.post("/admin/machines/{machine_id}/update")
def admin_machine_update(
    request: Request,
    machine_id: int,
    name: str = Form(...),
    kiosk_id: str = Form(...),
    location: str = Form(""),
    status: str = Form(...),
):
    redir = admin_required(request)
    if redir:
        return redir

    name = name.strip()
    kiosk_id = kiosk_id.strip()
    location = (location or "").strip() or None
    status = status.strip()

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE machines
                SET name=%s, kiosk_id=%s, location=%s, status=%s, updated_at=NOW()
                WHERE id=%s
                """,
                (name, kiosk_id, location, status, machine_id),
            )
        conn.commit()

    return RedirectResponse(f"/admin/machines/{machine_id}", status_code=303)


@app.post("/admin/machines/{machine_id}/req/add")
def admin_machine_req_add(request: Request, machine_id: int, cert_id: int = Form(...)):
    redir = admin_required(request)
    if redir:
        return redir

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO machine_requirements (machine_id, certification_id)
                VALUES (%s, %s)
                ON CONFLICT (machine_id, certification_id) DO NOTHING
                """,
                (machine_id, cert_id),
            )
        conn.commit()

    return RedirectResponse(f"/admin/machines/{machine_id}", status_code=303)


@app.post("/admin/machines/{machine_id}/req/remove")
def admin_machine_req_remove(request: Request, machine_id: int, cert_id: int = Form(...)):
    redir = admin_required(request)
    if redir:
        return redir

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM machine_requirements WHERE machine_id=%s AND certification_id=%s",
                (machine_id, cert_id),
            )
        conn.commit()

    return RedirectResponse(f"/admin/machines/{machine_id}", status_code=303)


@app.post("/admin/machines/{machine_id}/delete")
def admin_machine_delete(request: Request, machine_id: int):
    redir = admin_required(request)
    if redir:
        return redir

    try:
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM machines WHERE id=%s", (machine_id,))
            conn.commit()
        return RedirectResponse("/admin/machines", status_code=303)

    except Exception as e:
        # Re-render edit page with error
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, kiosk_id, location, status FROM machines WHERE id=%s", (machine_id,))
                row = cur.fetchone()
                if not row:
                    return RedirectResponse("/admin/machines", status_code=303)

                machine = {"id": row[0], "name": row[1], "kiosk_id": row[2], "location": row[3], "status": row[4]}

                cur.execute(
                    """
                    SELECT c.id, c.code, c.title
                    FROM machine_requirements mr
                    JOIN certifications c ON c.id = mr.certification_id
                    WHERE mr.machine_id=%s
                    ORDER BY c.code
                    """,
                    (machine_id,),
                )
                required = [{"id": r[0], "code": r[1], "title": r[2]} for r in cur.fetchall()]

                cur.execute("SELECT id, code, title FROM certifications ORDER BY code")
                all_certs = [{"id": r[0], "code": r[1], "title": r[2]} for r in cur.fetchall()]

        return templates.TemplateResponse(
            "admin_machine_edit.html",
            {
                "request": request,
                "machine": machine,
                "required": required,
                "all_certs": all_certs,
                "error": None,
                "delete_error": str(e),
            },
            status_code=400,
        )
@app.post("/admin/certs/{cert_id}/delete")
def admin_cert_delete(request: Request, cert_id: int):
    redir = admin_required(request)
    if redir:
        return redir

    try:
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute("DELETE FROM certifications WHERE id=%s", (cert_id,))
            conn.commit()
        return RedirectResponse("/admin/certs", status_code=303)

    except Exception as e:
        # Re-render cert list with error
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, code, title, description FROM certifications ORDER BY code")
                certs = [
                    {"id": r[0], "code": r[1], "title": r[2], "description": r[3]}
                    for r in cur.fetchall()
                ]

        return templates.TemplateResponse(
            "admin_certs.html",
            {"request": request, "certs": certs, "error": None, "delete_error": str(e)},
            status_code=400,
        )
@app.get("/admin/machines", response_class=HTMLResponse)
def admin_machines(request: Request):
    redir = admin_required(request)
    if redir:
        return redir

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, kiosk_id, location, status FROM machines ORDER BY name")
            machines = [
                {"id": r[0], "name": r[1], "kiosk_id": r[2], "location": r[3], "status": r[4]}
                for r in cur.fetchall()
            ]

    return templates.TemplateResponse(
        "admin_machines.html",
        {"request": request, "machines": machines, "error": None},
    )


@app.post("/admin/machines/create")
def admin_machines_create(request: Request, name: str = Form(...), kiosk_id: str = Form(...), location: str = Form("")):
    redir = admin_required(request)
    if redir:
        return redir

    name = name.strip()
    kiosk_id = kiosk_id.strip()
    location = (location or "").strip() or None

    try:
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    INSERT INTO machines (name, kiosk_id, location)
                    VALUES (%s, %s, %s)
                    """,
                    (name, kiosk_id, location),
                )
            conn.commit()
        return RedirectResponse("/admin/machines", status_code=303)

    except Exception as e:
        with db() as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT id, name, kiosk_id, location, status FROM machines ORDER BY name")
                machines = [
                    {"id": r[0], "name": r[1], "kiosk_id": r[2], "location": r[3], "status": r[4]}
                    for r in cur.fetchall()
                ]
        return templates.TemplateResponse(
            "admin_machines.html",
            {"request": request, "machines": machines, "error": str(e)},
            status_code=400,
        )


@app.get("/admin/machines/{machine_id}", response_class=HTMLResponse)
def admin_machine_edit(request: Request, machine_id: int):
    redir = admin_required(request)
    if redir:
        return redir

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute("SELECT id, name, kiosk_id, location, status FROM machines WHERE id=%s", (machine_id,))
            row = cur.fetchone()
            if not row:
                return RedirectResponse("/admin/machines", status_code=303)

            machine = {"id": row[0], "name": row[1], "kiosk_id": row[2], "location": row[3], "status": row[4]}

            cur.execute(
                """
                SELECT c.id, c.code, c.title
                FROM machine_requirements mr
                JOIN certifications c ON c.id = mr.certification_id
                WHERE mr.machine_id=%s
                ORDER BY c.code
                """,
                (machine_id,),
            )
            required = [{"id": r[0], "code": r[1], "title": r[2]} for r in cur.fetchall()]

            cur.execute("SELECT id, code, title FROM certifications ORDER BY code")
            all_certs = [{"id": r[0], "code": r[1], "title": r[2]} for r in cur.fetchall()]

    return templates.TemplateResponse(
        "admin_machine_edit.html",
        {"request": request, "machine": machine, "required": required, "all_certs": all_certs, "error": None},
    )


@app.post("/admin/machines/{machine_id}/update")
def admin_machine_update(
    request: Request,
    machine_id: int,
    name: str = Form(...),
    kiosk_id: str = Form(...),
    location: str = Form(""),
    status: str = Form(...),
):
    redir = admin_required(request)
    if redir:
        return redir

    name = name.strip()
    kiosk_id = kiosk_id.strip()
    location = (location or "").strip() or None
    status = status.strip()

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                UPDATE machines
                SET name=%s, kiosk_id=%s, location=%s, status=%s, updated_at=NOW()
                WHERE id=%s
                """,
                (name, kiosk_id, location, status, machine_id),
            )
        conn.commit()

    return RedirectResponse(f"/admin/machines/{machine_id}", status_code=303)


@app.post("/admin/machines/{machine_id}/req/add")
def admin_machine_req_add(request: Request, machine_id: int, cert_id: int = Form(...)):
    redir = admin_required(request)
    if redir:
        return redir

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                """
                INSERT INTO machine_requirements (machine_id, certification_id)
                VALUES (%s, %s)
                ON CONFLICT (machine_id, certification_id) DO NOTHING
                """,
                (machine_id, cert_id),
            )
        conn.commit()

    return RedirectResponse(f"/admin/machines/{machine_id}", status_code=303)


@app.post("/admin/machines/{machine_id}/req/remove")
def admin_machine_req_remove(request: Request, machine_id: int, cert_id: int = Form(...)):
    redir = admin_required(request)
    if redir:
        return redir

    with db() as conn:
        with conn.cursor() as cur:
            cur.execute(
                "DELETE FROM machine_requirements WHERE machine_id=%s AND certification_id=%s",
                (machine_id, cert_id),
            )
        conn.commit()

    return RedirectResponse(f"/admin/machines/{machine_id}", status_code=303)


# =========================
# Health
# =========================

@app.get("/health")
def health():
    return {"status": "ok"}
