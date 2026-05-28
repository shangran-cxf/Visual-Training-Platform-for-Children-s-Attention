import sqlite3

from flask import Blueprint, jsonify, request

from database import execute_db
from middleware import generate_token, require_auth
from utils import build_update_sql, error_response, success_response
from utils.password_utils import hash_password, is_bcrypt_hash, verify_password

auth_bp = Blueprint("auth", __name__)


def get_next_uid():
    result = execute_db("SELECT MAX(uid) FROM parents")
    max_uid = result[0][0] if result and result[0][0] else 99999
    return max_uid + 1


@auth_bp.route("/api/register", methods=["POST"])
def register():
    data = request.json
    username = data.get("username")
    password = data.get("password")
    email = data.get("email")
    children = data.get("children", [])

    if not username or not password:
        return error_response("用户名和密码不能为空", status=400)

    try:
        uid = get_next_uid()
        hashed_password = hash_password(password)
        result, parent_id = execute_db(
            "INSERT INTO parents (uid, username, password, email, role) VALUES (?, ?, ?, ?, ?)",
            (uid, username, hashed_password, email, "user"),
            fetch_last_id=True,
        )

        created_children = []
        for child in children:
            child_name = child.get("name")
            child_age = child.get("age")
            if child_name:
                _, child_id = execute_db(
                    "INSERT INTO children (parent_id, name, age) VALUES (?, ?, ?)",
                    (parent_id, child_name, child_age),
                    fetch_last_id=True,
                )
                created_children.append({"id": child_id, "name": child_name, "age": child_age})

        token = generate_token(parent_id, "user")

        return jsonify(
            {
                "parent_id": parent_id,
                "uid": uid,
                "token": token,
                "role": "user",
                "children": created_children,
            }
        ), 201
    except sqlite3.IntegrityError:
        return error_response("用户名已存在", status=400)


@auth_bp.route("/api/login", methods=["POST"])
def login():
    data = request.json
    username = data.get("username")
    password = data.get("password")

    if not username or not password:
        return error_response("用户名和密码不能为空", status=400)

    result = execute_db(
        "SELECT id, uid, email, role, is_banned, avatar, password FROM parents WHERE username = ?", (username,)
    )

    if not result:
        return error_response("用户名或密码错误", status=401)

    parent_id, uid, email, role, is_banned, avatar, stored_password = result[0]

    if is_banned == 1:
        return error_response("账户已封禁", status=403)

    password_valid = False
    need_upgrade = False

    if is_bcrypt_hash(stored_password):
        password_valid = verify_password(password, stored_password)
    else:
        if stored_password == password:
            password_valid = True
            need_upgrade = True

    if not password_valid:
        return error_response("用户名或密码错误", status=401)

    if need_upgrade:
        hashed_password = hash_password(password)
        execute_db("UPDATE parents SET password = ? WHERE id = ?", (hashed_password, parent_id))

    children = execute_db("SELECT id, name, age FROM children WHERE parent_id = ?", (parent_id,))

    children_data = [{"id": c[0], "name": c[1], "age": c[2]} for c in children]

    token = generate_token(parent_id, role)

    return jsonify(
        {
            "parent_id": parent_id,
            "uid": uid,
            "username": username,
            "role": role,
            "avatar": avatar,
            "children": children_data,
            "token": token,
        }
    ), 200


@auth_bp.route("/api/user/query", methods=["GET"])
@require_auth
def query_user():
    query_type = request.args.get("type")
    value = request.args.get("value")

    if not query_type or not value:
        return error_response("缺少type或value参数", status=400)

    if query_type not in ["id", "uid", "username"]:
        return error_response("type参数必须是id、uid或username", status=400)

    if query_type == "id":
        result = execute_db(
            "SELECT id, uid, username, email, role, avatar, created_at FROM parents WHERE id = ?", (value,)
        )
    elif query_type == "uid":
        result = execute_db(
            "SELECT id, uid, username, email, role, avatar, created_at FROM parents WHERE uid = ?", (value,)
        )
    else:
        result = execute_db(
            "SELECT id, uid, username, email, role, avatar, created_at FROM parents WHERE username = ?", (value,)
        )

    if not result:
        return error_response("用户不存在", status=404)

    row = result[0]
    return success_response(
        {
            "id": row[0],
            "uid": row[1],
            "username": row[2],
            "email": row[3],
            "role": row[4],
            "avatar": row[5],
            "created_at": row[6],
        }
    )


@auth_bp.route("/api/user/change-password", methods=["POST"])
@require_auth
def change_password():
    data = request.json
    old_password = data.get("old_password")
    new_password = data.get("new_password")

    if not old_password or not new_password:
        return error_response("参数不完整", status=400)

    user = execute_db("SELECT id, password FROM parents WHERE id = ?", (request.user_id,))
    stored_password = user[0][1]
    password_valid = False

    if is_bcrypt_hash(stored_password):
        password_valid = verify_password(old_password, stored_password)
    else:
        password_valid = stored_password == old_password

    if not password_valid:
        return error_response("旧密码错误", status=400)

    hashed_password = hash_password(new_password)
    execute_db("UPDATE parents SET password = ? WHERE id = ?", (hashed_password, request.user_id))
    return success_response(None, "密码修改成功")


@auth_bp.route("/api/verify-password", methods=["POST"])
@auth_bp.route("/api/user/verify-password", methods=["POST"])
@require_auth
def verify_password_endpoint():
    data = request.json
    password = data.get("password") or data.get("old_password")

    if not password:
        return error_response("参数不完整", status=400)

    result = execute_db("SELECT id, password FROM parents WHERE id = ?", (request.user_id,))

    if not result:
        return jsonify({"valid": False}), 200

    stored_password = result[0][1]
    password_valid = False

    if is_bcrypt_hash(stored_password):
        password_valid = verify_password(password, stored_password)
    else:
        password_valid = stored_password == password

    return jsonify({"valid": password_valid}), 200


@auth_bp.route("/api/user/update", methods=["POST"])
@auth_bp.route("/api/user/update-profile", methods=["POST"])
@require_auth
def update_user_info():
    data = request.json
    username = data.get("username")
    email = data.get("email")
    avatar = data.get("avatar")
    old_password = data.get("old_password")
    new_password = data.get("password")

    update_data = {}

    if username is not None:
        existing = execute_db("SELECT id FROM parents WHERE username = ? AND id != ?", (username, request.user_id))
        if existing:
            return error_response("用户名已被使用", status=400)
        update_data["username"] = username

    if email is not None:
        import re

        if not re.match(r"^[^\s@]+@[^\s@]+\.[^\s@]+$", email):
            return error_response("邮箱格式不正确", status=400)
        update_data["email"] = email

    if avatar is not None:
        update_data["avatar"] = avatar

    if new_password:
        user = execute_db("SELECT password FROM parents WHERE id = ?", (request.user_id,))
        stored_password = user[0][0] if user else None
        password_valid = False

        if stored_password:
            if is_bcrypt_hash(stored_password):
                password_valid = verify_password(old_password or "", stored_password)
            else:
                password_valid = stored_password == (old_password or "")

        if not password_valid:
            return error_response("旧密码错误", status=400)

        update_data["password"] = hash_password(new_password)

    if not update_data:
        return error_response("没有需要更新的字段", status=400)

    sql, params = build_update_sql("parents", update_data, "id = ?")
    execute_db(sql, params + (request.user_id,))

    return success_response(None, "更新成功")


@auth_bp.route("/api/user/avatar", methods=["POST"])
@require_auth
def upload_avatar():
    import os

    from PIL import Image

    if "avatar" not in request.files:
        return error_response("缺少头像文件", status=400)

    file = request.files["avatar"]
    if file.filename == "":
        return error_response("没有选择文件", status=400)

    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > 5 * 1024 * 1024:
        return error_response("文件大小不能超过5MB", status=400)

    try:
        img = Image.open(file.stream)
        img.verify()
        file.seek(0)
        img = Image.open(file.stream)
    except Exception:
        return error_response("无效的图片文件", status=400)

    if img.format not in ("PNG", "JPEG", "GIF", "WEBP"):
        return error_response("不支持的文件格式，仅允许 png/jpg/jpeg/gif/webp", status=400)

    upload_folder = os.path.join(os.path.dirname(os.path.dirname(__file__)), "uploads")
    if not os.path.exists(upload_folder):
        os.makedirs(upload_folder)

    filename = f"{request.user_id}.jpg"
    file_path = os.path.join(upload_folder, filename)

    if img.mode in ("RGBA", "P", "LA"):
        img = img.convert("RGBA")
        background = Image.new("RGBA", img.size, (255, 255, 255, 255))
        img = Image.alpha_composite(background, img)
    img = img.convert("RGB")

    # 居中裁剪为正方形
    min_dim = min(img.width, img.height)
    left = (img.width - min_dim) // 2
    top = (img.height - min_dim) // 2
    img = img.crop((left, top, left + min_dim, top + min_dim))

    max_dim = 500
    if min_dim > max_dim:
        img = img.resize((max_dim, max_dim), Image.LANCZOS)

    img.save(file_path, "JPEG", quality=85)

    avatar_url = f"/uploads/{filename}"

    execute_db("UPDATE parents SET avatar = ? WHERE id = ?", (avatar_url, request.user_id))

    return success_response({"avatar_url": avatar_url}, "头像上传成功")
