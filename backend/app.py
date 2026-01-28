from datetime import datetime, timedelta
import os
import jwt
from functools import wraps
from flask import Flask, jsonify, request, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
from werkzeug.security import generate_password_hash, check_password_hash
from werkzeug.utils import secure_filename
from models import db, User, Transaction, TransactionSplit, SettlementSession, HistoricalSettlement
from ocr import get_ocr_service
from bank_parser import BankParser
from sqlalchemy import func
from flask_migrate import Migrate

load_dotenv(os.path.join(os.path.dirname(os.path.dirname(__file__)), ".env"))

app = Flask(__name__)
CORS(app)

app.config["SECRET_KEY"] = os.getenv("SECRET_KEY", "dev-secret-key-12345")
UPLOAD_FOLDER = "uploads"
AVATAR_FOLDER = "avatars"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(AVATAR_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER
app.config["AVATAR_FOLDER"] = AVATAR_FOLDER
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024

db_user = os.getenv("POSTGRES_USER", "wbw_admin")
db_pass = os.getenv("POSTGRES_PASSWORD", "secure_wbw_password_2026")
db_host = "localhost"
db_port = "5432"
db_name = os.getenv("POSTGRES_DB", "better_wbw")

app.config["SQLALCHEMY_DATABASE_URI"] = f"postgresql://{db_user}:{db_pass}@{db_host}:{db_port}/{db_name}"
app.config["SQLALCHEMY_TRACK_MODIFICATIONS"] = False
app.config["SQLALCHEMY_ENGINE_OPTIONS"] = {"pool_pre_ping": True}

db.init_app(app)
migrate = Migrate(app, db)

def token_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        token = None
        if "Authorization" in request.headers:
            ah = request.headers["Authorization"]
            if ah.startswith("Bearer "): token = ah.split(" ")[1]
        if not token: return jsonify({"message": "Missing token"}), 401
        try:
            data = jwt.decode(token, app.config["SECRET_KEY"], algorithms=["HS256"])
            user = db.session.get(User, data["user_id"])
            if not user: return jsonify({"message": "User not found"}), 401
        except Exception as e: return jsonify({"message": "Invalid token", "error": str(e)}), 401
        return f(user, *args, **kwargs)
    return decorated

@app.route("/")
def health():
    return jsonify({"status": "ok"})

@app.route("/seed-db")
def seed_db():
    try:
        # Check if users already exist to avoid duplicates
        if User.query.first():
            return jsonify({"message": "Database already seeded"}), 200
            
        pw = generate_password_hash('wbw2026')
        
        m1 = User(); m1.name='Arjan'; m1.email='arjan@example.com'; m1.avatar_url='http://127.0.0.1:5000/static/user_1_1636579358798.jpeg'; m1.is_group_member=True; m1.password_hash=pw
        m2 = User(); m2.name='Emma'; m2.email='emma@example.com'; m2.avatar_url='https://i.pravatar.cc/150?u=emma'; m2.is_group_member=True; m2.password_hash=pw
        m3 = User(); m3.name='Lars'; m3.email='lars@example.com'; m3.avatar_url='https://i.pravatar.cc/150?u=lars'; m3.is_group_member=True; m3.password_hash=pw
        m4 = User(); m4.name='Friend'; m4.is_group_member=False; m4.email=None; m4.password_hash=None
        db.session.add_all([m1, m2, m3, m4]); db.session.flush()

        today = datetime.utcnow().date()
        yesterday = today - timedelta(days=1)
        last_week = today - timedelta(days=7)
        
        t1 = Transaction(); t1.description="Lunch bij Loetje"; t1.amount=65.50; t1.date=today; t1.payer_id=m1.id; t1.type='EXPENSE'
        db.session.add(t1); db.session.flush()
        for u in [m1, m2, m3]: 
            s = TransactionSplit(); s.transaction_id=t1.id; s.user_id=u.id; s.weight=1; db.session.add(s)
        
        t2 = Transaction(); t2.description="Boodschappen AH"; t2.amount=42.10; t2.date=yesterday; t2.payer_id=m2.id; t2.type='EXPENSE'
        db.session.add(t2); db.session.flush()
        for u in [m1, m2]: 
            s = TransactionSplit(); s.transaction_id=t2.id; s.user_id=u.id; s.weight=1; db.session.add(s)
        
        t3 = Transaction(); t3.description="Benzine"; t3.amount=85.00; t3.date=last_week; t3.payer_id=m3.id; t3.type='EXPENSE'
        db.session.add(t3); db.session.flush()
        s3a = TransactionSplit(); s3a.transaction_id=t3.id; s3a.user_id=m1.id; s3a.weight=2; db.session.add(s3a)
        s3b = TransactionSplit(); s3b.transaction_id=t3.id; s3b.user_id=m3.id; s3b.weight=1; db.session.add(s3b)
        
        db.session.commit()
        return jsonify({"status": "success", "message": "Seed complete"})
    except Exception as e: 
        db.session.rollback(); return jsonify({"error": str(e)}), 500

@app.route("/login", methods=["POST"])
def login():
    auth = request.json
    if not auth: return jsonify({"message": "Missing"}), 400
    u_lower = auth["username"].lower()
    user = User.query.filter((func.lower(User.name) == u_lower) | (func.lower(User.email) == u_lower)).first()
    if not user or not user.password_hash or not check_password_hash(user.password_hash, auth["password"]):
        return jsonify({"message": "Invalid"}), 401
    tk = jwt.encode({"user_id": user.id, "exp": datetime.utcnow() + timedelta(hours=24)}, app.config["SECRET_KEY"], algorithm="HS256")
    return jsonify({"token": tk, "user": {"id": user.id, "name": user.name, "email": user.email, "avatar_url": user.avatar_url}})

@app.route('/users', methods=['GET'])
@token_required
def get_users(current_user):
    return jsonify([{"id": u.id, "name": u.name, "email": u.email, "avatar_url": u.avatar_url, "is_group_member": u.is_group_member} for u in User.query.all()])

@app.route('/users/profile', methods=['PUT'])
@token_required
def update_profile(current_user):
    d = request.json
    if 'avatar_url' in d: current_user.avatar_url = d['avatar_url']
    if 'name' in d: current_user.name = d['name']
    if 'email' in d: current_user.email = d['email']
    db.session.commit()
    return jsonify({"status": "success", "user": {"id": current_user.id, "name": current_user.name, "email": current_user.email, "avatar_url": current_user.avatar_url}})

@app.route('/users/avatar', methods=['POST'])
@token_required
def upload_avatar(current_user):
    f = request.files.get('file')
    if not f or not f.filename: return jsonify({"error": "No file"}), 400
    fn = f"user_{current_user.id}_{secure_filename(f.filename)}"
    f.save(os.path.join(app.config['AVATAR_FOLDER'], fn))
    current_user.avatar_url = f"http://127.0.0.1:5000/static/{fn}"
    db.session.commit()
    return jsonify({"status": "success", "avatar_url": current_user.avatar_url, "user": {"id": current_user.id, "name": current_user.name, "avatar_url": current_user.avatar_url}})

@app.route('/static/<path:filename>')
def serve_static(filename):
    if os.path.exists(os.path.join(app.config['AVATAR_FOLDER'], filename)):
        return send_from_directory(app.config['AVATAR_FOLDER'], filename)
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)

@app.route('/balances', methods=['GET'])
@token_required
def get_balances(current_user):
    users = User.query.all(); txs = Transaction.query.filter_by(settlement_session_id=None).all(); bals = {u.id: 0.0 for u in users}
    for t in txs:
        amt = t.amount; tp = t.type or "EXPENSE"
        if t.payer_id in bals:
            if tp in ["EXPENSE", "TRANSFER"]: bals[t.payer_id] += amt
            else: bals[t.payer_id] -= amt
        tw = sum(s.weight for s in t.splits)
        if tw > 0:
            ppw = amt / tw
            for s in t.splits:
                if s.user_id in bals:
                    if tp in ["EXPENSE", "TRANSFER"]: bals[s.user_id] -= ppw * s.weight
                    else: bals[s.user_id] += ppw * s.weight
    return jsonify([{"user_id": uid, "balance": round(bal, 2)} for uid, bal in bals.items()])

@app.route('/transactions', methods=['GET'])
@token_required
def get_transactions(current_user):
    txs = Transaction.query.filter_by(settlement_session_id=None).order_by(Transaction.date.desc()).all()
    return jsonify([{"id": t.id, "date": t.date.isoformat(), "description": t.description, "amount": t.amount, "type": t.type or "EXPENSE", "payer_id": t.payer_id, "splits": [{"user_id": s.user_id, "weight": s.weight} for s in t.splits]} for t in txs])

@app.route('/transactions', methods=['POST'])
@token_required
def add_transaction(current_user):
    d = request.json
    try:
        t = Transaction(); t.description = d['description']; t.amount = float(d['amount']); t.type = d.get('type', 'EXPENSE')
        t.date = datetime.strptime(d['date'], '%Y-%m-%d').date() if isinstance(d.get('date'), str) else datetime.utcnow().date()
        t.payer_id = d['payer_id']
        db.session.add(t); db.session.flush()
        for s_data in d['splits']:
            split = TransactionSplit(); split.transaction_id=t.id; split.user_id=s_data['user_id']; split.weight=s_data.get('weight', 1)
            db.session.add(split)
        db.session.commit()
        return jsonify({"status": "success", "id": t.id})
    except Exception as e: db.session.rollback(); return jsonify({"error": str(e)}), 500

@app.route('/transactions/<int:tx_id>', methods=['PUT'])
@token_required
def update_transaction(current_user, tx_id):
    d = request.json
    try:
        t = db.session.get(Transaction, tx_id)
        if not t: return jsonify({"error": "Not found"}), 404
        t.description = d['description']; t.amount = float(d['amount']); t.type = d.get('type', 'EXPENSE')
        if isinstance(d.get('date'), str): t.date = datetime.strptime(d['date'], '%Y-%m-%d').date()
        t.payer_id = d['payer_id']
        TransactionSplit.query.filter_by(transaction_id=tx_id).delete()
        for s_data in d['splits']:
            split = TransactionSplit(); split.transaction_id=tx_id; split.user_id=s_data['user_id']; split.weight=s_data.get('weight', 1)
            db.session.add(split)
        db.session.commit(); return jsonify({"status": "success"})
    except Exception as e: db.session.rollback(); return jsonify({"error": str(e)}), 500

@app.route('/transactions/<int:tx_id>', methods=['DELETE'])
@token_required
def delete_transaction(current_user, tx_id):
    try:
        t = db.session.get(Transaction, tx_id)
        if t: db.session.delete(t); db.session.commit()
        return jsonify({"status": "success"})
    except Exception as e: db.session.rollback(); return jsonify({"error": str(e)}), 500

@app.route('/settlements/suggest', methods=['GET'])
@token_required
def suggest_settlement(current_user):
    users = User.query.all(); txs = Transaction.query.filter_by(settlement_session_id=None).all(); bals = {u.id: 0.0 for u in users}
    for t in txs:
        amt = t.amount; tp = t.type or "EXPENSE"
        if t.payer_id in bals:
            if tp in ["EXPENSE", "TRANSFER"]: bals[t.payer_id] += amt
            else: bals[t.payer_id] -= amt
        tw = sum(s.weight for s in t.splits)
        if tw > 0:
            ppw = amt / tw
            for s in t.splits:
                if s.user_id in bals:
                    if tp in ["EXPENSE", "TRANSFER"]: bals[s.user_id] -= ppw * s.weight
                    else: bals[s.user_id] += ppw * s.weight
    u_map = {u.id: u.name for u in users}
    dbtr = [[uid, abs(bal)] for uid, bal in bals.items() if bal < -0.01]
    crtr = [[uid, bal] for uid, bal in bals.items() if bal > 0.01]
    dbtr.sort(key=lambda x: x[1], reverse=True); crtr.sort(key=lambda x: x[1], reverse=True)
    res, d_i, c_i = [], 0, 0
    while d_i < len(dbtr) and c_i < len(crtr):
        amt = min(dbtr[d_i][1], crtr[c_i][1])
        res.append({"from_user_id": dbtr[d_i][0], "from_user": u_map[dbtr[d_i][0]], "to_user_id": crtr[c_i][0], "to_user": u_map[crtr[c_i][0]], "amount": round(amt, 2)})
        dbtr[d_i][1] -= amt; crtr[c_i][1] -= amt
        if dbtr[d_i][1] < 0.01: d_i += 1
        if crtr[c_i][1] < 0.01: c_i += 1
    return jsonify(res)

@app.route('/settlements/commit', methods=['POST'])
@token_required
def commit_settlement(current_user):
    try:
        suggestions = suggest_settlement(current_user).get_json()
        if not suggestions: return jsonify({"message": "Nothing to settle"}), 400
        sess = SettlementSession(); sess.description = f"Verrekening door {current_user.name}"; db.session.add(sess); db.session.flush()
        unsettled = Transaction.query.filter_by(settlement_session_id=None).all()
        for t in unsettled: t.settlement_session_id = sess.id
        for s in suggestions:
            hs = HistoricalSettlement(); hs.settlement_session_id = sess.id; hs.from_user_id = s['from_user_id']; hs.to_user_id = s['to_user_id']; hs.amount = s['amount']; db.session.add(hs)
        db.session.commit(); return jsonify({"status": "success", "session_id": sess.id})
    except Exception as e: db.session.rollback(); return jsonify({"error": str(e)}), 500

@app.route('/settlements/history', methods=['GET'])
@token_required
def get_settlement_history(current_user):
    sessions = SettlementSession.query.order_by(SettlementSession.date.desc()).all()
    res = []
    for s in sessions:
        total = sum(h.amount for h in s.results)
        res.append({"id": s.id, "date": s.date.isoformat(), "description": s.description, "total_amount": round(total, 2), "results": [{"from_user": h.from_user.name, "to_user": h.to_user.name, "amount": h.amount} for h in s.results]})
    return jsonify(res)

@app.route("/import/bank", methods=["POST"])
@token_required
def import_bank(current_user):
    if "file" not in request.files: return jsonify({"error": "No file"}), 400
    bank_type = request.form.get("bank_type", "ing")
    content = request.files["file"].read().decode('utf-8')
    try:
        data = BankParser.parse_ing_csv(content) if bank_type == "ing" else BankParser.parse_abn_csv(content)
        return jsonify({"status": "success", "transactions": data})
    except Exception as e: return jsonify({"error": str(e)}), 500

@app.route("/ocr/process", methods=["POST"])
@token_required
def process_receipt(current_user):
    f = request.files.get("file")
    if not f or not f.filename: return jsonify({"error": "No file"}), 400
    fn = secure_filename(f.filename)
    fp = os.path.join(app.config["UPLOAD_FOLDER"], fn); f.save(fp)
    try:
        return jsonify({"status": "success", "data": get_ocr_service().process_receipt(fp)})
    except Exception as e: return jsonify({"error": str(e)}), 500

if __name__ == "__main__":
    app.run(debug=True, port=5001)
