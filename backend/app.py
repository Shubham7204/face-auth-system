from flask import Flask, request, jsonify
from deepface import DeepFace
import os
from flask_cors import CORS
import cv2
import time as import_time
import shutil

app = Flask(__name__)
CORS(app)

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
BANK_PATH = os.path.join(BASE_DIR, "stored_images", "user_bank.jpeg")
LAST_VERIFIED_PATH = os.path.join(BASE_DIR, "stored_images", "last_verified.jpg")
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

def save_verified_image(temp_image_path):
    """Save the successfully verified image for future verification"""
    try:
        shutil.copy2(temp_image_path, LAST_VERIFIED_PATH)
        print(f"✅ Saved verified image for future use at: {LAST_VERIFIED_PATH}")
        return True
    except Exception as e:
        print(f"❌ Error saving verified image: {str(e)}")
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
        # Determine which reference image to use
        is_first_login = not os.path.exists(LAST_VERIFIED_PATH)
        reference_image = BANK_PATH if is_first_login else LAST_VERIFIED_PATH
        verification_type = "bank" if is_first_login else "previous"
        
        try:
            print(f"Attempting face verification with {verification_type} image")
            result = DeepFace.verify(
                img1_path=live_image_path, 
                img2_path=reference_image, 
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
            "is_first_login": is_first_login,
            "verification_details": {
                "face_verified": face_score >= threshold,
                "verification_type": verification_type,
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
            
            # If this was a successful verification, save the image for future use
            if save_verified_image(live_image_path):
                response_data["verification_details"]["image_saved"] = True
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

@app.route("/reset", methods=["POST"])
def reset_verification():
    """Reset the verification by removing the last verified image"""
    try:
        if os.path.exists(LAST_VERIFIED_PATH):
            os.remove(LAST_VERIFIED_PATH)
        return jsonify({
            "status": "success",
            "message": "Verification reset successful"
        })
    except Exception as e:
        return jsonify({
            "status": "error",
            "message": f"Error resetting verification: {str(e)}"
        })

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