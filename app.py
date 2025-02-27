from flask import render_template, request, redirect, url_for, flash, jsonify
from datetime import datetime
from config import app, db
from models import Issue, User
from flask_login import LoginManager, login_user, logout_user, login_required, current_user

login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

class TestEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    message = db.Column(db.String(100), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        user = User.query.filter_by(email=request.form['email']).first()
        if user and user.check_password(request.form['password']):
            login_user(user)
            return redirect(url_for('index'))
        flash('Invalid email or password', 'error')
    return render_template('login.html')

@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        if User.query.filter_by(email=request.form['email']).first():
            flash('Email already registered', 'error')
            return render_template('register.html')
        
        user = User(email=request.form['email'], name=request.form['name'])
        user.set_password(request.form['password'])
        db.session.add(user)
        db.session.commit()
        flash('Registration successful! Please login.', 'success')
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/logout')
@login_required
def logout():
    logout_user()
    return redirect(url_for('index'))

@app.route('/issues')
def issues():
    issues = Issue.query.order_by(Issue.reported_at.desc()).all()
    return render_template('issues.html', issues=issues)

@app.route('/issues/new', methods=['GET', 'POST'])
def new_issue():
    if request.method == 'POST':
        issue = Issue(
            title=request.form['title'],
            description=request.form['description'],
            issue_type=request.form['issue_type'],
            severity=request.form['severity'],
            reported_by=current_user.name if current_user.is_authenticated else 'Anonymous'
        )
        db.session.add(issue)
        db.session.commit()
        flash('Issue reported successfully!', 'success')
        return redirect(url_for('issues'))
    return render_template('new_issue.html')

@app.route('/api/test', methods=['POST'])
def test_connection():
    try:
        message = request.form.get('message', 'Test Message')
        new_entry = TestEntry(message=message)
        db.session.add(new_entry)
        db.session.commit()
        return jsonify({'status': 'success', 'message': 'Database connection successful!'})
    except Exception as e:
        return jsonify({'status': 'error', 'message': str(e)})

@app.route('/api/entries')
def get_entries():
    entries = TestEntry.query.order_by(TestEntry.created_at.desc()).all()
    return jsonify([{'id': entry.id, 'message': entry.message, 'created_at': entry.created_at.strftime('%Y-%m-%d %H:%M:%S')} for entry in entries])

@app.route('/issues/<int:id>')
def view_issue(id):
    issue = Issue.query.get_or_404(id)
    return render_template('view_issue.html', issue=issue)

@app.route('/issues/<int:id>/close', methods=['POST'])
@login_required
def close_issue(id):
    issue = Issue.query.get_or_404(id)
    issue.close()
    db.session.commit()
    flash('Issue has been closed successfully.', 'success')
    return redirect(url_for('view_issue', id=id))

@app.route('/issues/<int:id>/reopen', methods=['POST'])
@login_required
def reopen_issue(id):
    issue = Issue.query.get_or_404(id)
    issue.reopen()
    db.session.commit()
    flash('Issue has been reopened successfully.', 'success')
    return redirect(url_for('view_issue', id=id))

@app.route('/profile')
@login_required
def profile():
    user_issues = Issue.query.filter_by(reported_by=current_user.name).order_by(Issue.reported_at.desc()).all()
    return render_template('profile.html', issues=user_issues)

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(debug=True)