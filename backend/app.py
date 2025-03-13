from flask import Flask, request, jsonify
from deepface import DeepFace
import os
from flask_cors import CORS
import cv2
import time as import_time

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANK_PATH = os.path.join(BASE_DIR, "stored_images", "user_bank.jpeg")
THRESHOLD = 0.65

def test_image(image_path, label):
    try:
        img = cv2.imread(image_path)
        if img is None:
            print(f"❌ {label} image could not be loaded with OpenCV")
            return False
        else:
            print(f"✅ {label} image loaded successfully with OpenCV (dimensions: {img.shape})")
            return True
    except Exception as e:
        print(f"❌ Error loading {label} image: {str(e)}")
        return False

print(f"Looking for Bank image at: {BANK_PATH}")
print(f"Bank image exists: {os.path.exists(BANK_PATH)}")

print("\n--- Verifying Stored Images ---")
if not test_image(BANK_PATH, "Bank"):
    print("⚠️ Bank image is invalid or missing")
print("----------------------------\n")

@app.route("/verify", methods=["POST"])
def verify_user():
    if "live_image" not in request.files:
        return jsonify({"status": "error", "message": "No file uploaded"}), 400
    
    live_image = request.files["live_image"]
    live_image_path = os.path.join(BASE_DIR, "temp_live.jpg")
    live_image.save(live_image_path)
    
    if not os.path.exists(live_image_path):
        print(f"❌ Live image not saved at: {live_image_path}")
        return jsonify({"status": "error", "message": "Live image not saved"}), 500
    
    print(f"✅ Live image saved at: {live_image_path}, size: {os.path.getsize(live_image_path)} bytes")
    
    if not test_image(live_image_path, "Live capture"):
        return jsonify({"status": "error", "message": "Could not process captured image"}), 400
    
    try:
        try:
            print(f"Attempting face verification with live image: {live_image_path}")
            result = DeepFace.verify(
                img1_path=live_image_path, 
                img2_path=BANK_PATH, 
                model_name="Facenet",
                enforce_detection=False
            )
            face_score = round((1 - result["distance"]) * 100, 2)
            print(f"Face verification successful - Score: {face_score}%")
        except Exception as e:
            print(f"Face verification failed: {str(e)}")
            face_score = 0
        
        threshold = round(THRESHOLD * 100, 2)
        
        response_data = {
            "face_score": face_score,
            "threshold": threshold,
            "verification_details": {
                "face_verified": face_score >= threshold,
                "timestamp": import_time.strftime("%Y-%m-%d %H:%M:%S")
            }
        }
        
        if face_score >= threshold:
            response_data["status"] = "success"
            response_data["message"] = "Authentication Successful"
            response_data["auth_result"] = {
                "success": True,
                "score": face_score,
                "log_message": f"User authenticated successfully with score {face_score}%"
            }
        else:
            response_data["status"] = "failed"
            response_data["message"] = "Authentication Failed"
            response_data["auth_result"] = {
                "success": False,
                "score": face_score,
                "log_message": f"Authentication failed. Score {face_score}% below threshold {threshold}%"
            }
        
        return jsonify(response_data)
    
    except Exception as e:
        print(f"Error during verification: {str(e)}")
        return jsonify({"status": "error", "message": str(e)})
    
    finally:
        if os.path.exists(live_image_path):
            os.remove(live_image_path)

@app.route("/test", methods=["GET"])
def test_endpoint():
    return jsonify({"status": "success", "message": "Server is running"}), 200

if __name__ == "__main__":
    os.makedirs(os.path.join(BASE_DIR, "stored_images"), exist_ok=True)
    print("Testing DeepFace installation...")
    try:
        models = DeepFace.build_model("Facenet")
        print(f"✅ DeepFace model loaded successfully: {type(models)}")
    except Exception as e:
        print(f"❌ Error loading DeepFace model: {str(e)}")
    app.run(debug=True)