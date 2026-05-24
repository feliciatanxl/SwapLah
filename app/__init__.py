from flask import Flask, render_template

def create_app():
    app = Flask(__name__)
    app.config['SECRET_KEY'] = 'your-secret-key'  # later move to .env

    @app.route('/')
    def index():
        return render_template('index.html')

    @app.route('/listing/<int:listing_id>')
    def listing_detail(listing_id):
        return render_template('listing_detail.html', listing_id=listing_id)

    @app.route('/offers')
    def offers():
        return render_template('offers.html')

    @app.route('/history')
    def history():
        return render_template('history.html')

    @app.route('/profile')
    def profile():
        return render_template('profile.html')

    @app.route('/profile/edit')
    def edit_profile():
        return render_template('edit_profile.html')

    @app.route('/sell')
    def sell():
        return render_template('sell.html')

    @app.route('/admin')
    def admin():
        return render_template('admin.html')

    return app
