from flask import Flask, render_template, request, redirect, url_for, session, jsonify

def configure_routes(app):

    @app.route('/', methods=['GET', 'POST'])
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
      
    @app.route('/contact', methods=['POST'])
    def index():
        return render_template('contact.html')

    @app.route('/subscribe', methods=['POST'])
    def index():
        return render_template('subscribe.html')
      
    @app.route('/account', methods=['POST'])
    def index():
        return render_template('account.html')

    @app.route('/cancel', methods=['POST'])
    def index():
        return render_template('cancel.html')



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
