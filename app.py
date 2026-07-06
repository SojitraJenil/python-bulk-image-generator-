from __future__ import annotations

from flask import Flask, jsonify
from routes import main_bp, bulk_image_bp, pose_generator_bp, upscaler_bp

def create_app() -> Flask:
    app = Flask(__name__)
    
    # Configure Max Upload Size (16 MB)
    app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
    
    # Register Application Blueprints
    app.register_blueprint(main_bp)
    app.register_blueprint(bulk_image_bp)
    app.register_blueprint(pose_generator_bp)
    app.register_blueprint(upscaler_bp)
    
    # Global Request Size Error Handler
    @app.errorhandler(413)
    def handle_request_too_large(_error):
        return jsonify({
            "error": "The uploaded image is too large. Please choose a file smaller than 16 MB."
        }), 413
        
    return app

app = create_app()

if __name__ == "__main__":
    print("\n[OMNIAI] Starting development server over standard HTTP.")
    print("[OMNIAI] Open: http://127.0.0.1:5000\n")
    app.run(debug=True, host="127.0.0.1", port=5000)