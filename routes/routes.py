from flask import Flask, render_template, request, redirect, url_for, session, jsonify

def configure_routes(app):

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/terms')
    def index():
        return render_template('terms.html')

    @app.route('/privacy')
    def index():
        return render_template('privacy.html')

    @app.route('/about')
    def index():
        return render_template('about.html')

    @app.route('/faq')
    def index():
        return render_template('faq.html')
      
    @app.route('/contact')
    def index():
        return render_template('contact.html')

    @app.route('/subscribe')
    def index():
        return render_template('subscribe.html')
    @app.route('/')

  
  
  
  def index():
        return render_template('index.html')

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/login', methods=['GET', 'POST'])
    def login():
        # Add your login logic here
        if request.method == 'POST':
            # Check credentials
            session['logged_in'] = True
            return redirect(url_for('dashboard'))
        return render_template('login.html')

    @app.route('/dashboard')
    def dashboard():
        if not session.get('logged_in'):
            return redirect(url_for('login'))
        return render_template('dashboard.html')

    @app.route('/api/data')
    def api_data():
        if not session.get('logged_in'):
            return jsonify({'error': 'unauthorized'}), 401
        # Return some data as JSON
        return jsonify({'data': 'Here is your data'})
