"""
Flask App Proxy for Tweet Extractors

This application serves as a proxy to the tweet extractor services running on Railway.
It forwards requests to the backend APIs and returns the responses.
"""

from flask import Flask, request, jsonify
import requests
import os
import time

app = Flask(__name__)

# Get backend URLs from environment variables
TWEET_EXTRACTOR_URL = os.environ.get('TWEET_EXTRACTOR_URL')
EXTRACTORT_URL = os.environ.get('EXTRACTORT_URL')  # New variable for ExtractorT

if not TWEET_EXTRACTOR_URL:
    raise EnvironmentError("TWEET_EXTRACTOR_URL environment variable is not set")
if not EXTRACTORT_URL:
    raise EnvironmentError("EXTRACTORT_URL environment variable is not set")

@app.route('/')
def index():
    """Display a simple message on the root path."""
    return jsonify({
        "name": "Tweet Extractor API Gateway",
        "description": "This service forwards requests to the Tweet Extractor APIs running on Railway.",
        "endpoints": [
            "/extract", 
            "/extract-batch", 
            "/extractT/hashtag/{hashtag}", 
            "/extractT/user/{username}", 
            "/health"
        ]
    })

@app.route('/extract', methods=['POST'])
def extract():
    """Forward extract request to the backend service."""
    try:
        # Forward the request data to the backend
        response = requests.post(
            f"{TWEET_EXTRACTOR_URL}/extract",
            json=request.json,
            headers={'Content-Type': 'application/json'},
            timeout=15
        )
        
        # Return the response from the backend
        return jsonify(response.json()), response.status_code
            
    except requests.RequestException as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to connect to the backend service: {str(e)}"
        }), 500

@app.route('/extract-batch', methods=['POST'])
def extract_batch():
    """Forward batch extraction request to the backend service."""
    try:
        # Forward the request data to the backend
        response = requests.post(
            f"{TWEET_EXTRACTOR_URL}/extract-batch",
            json=request.json,
            headers={'Content-Type': 'application/json'},
            timeout=30
        )
        
        # Return the response from the backend
        return jsonify(response.json()), response.status_code
            
    except requests.RequestException as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to connect to the backend service: {str(e)}"
        }), 500

@app.route('/extractT/hashtag/<hashtag>', methods=['GET'])
def extract_hashtag(hashtag):
    """Forward hashtag extraction request to the ExtractorT service."""
    try:
        # Get query parameters
        max_tweets = request.args.get('max_tweets', 30)
        min_tweets = request.args.get('min_tweets', 10)
        max_scrolls = request.args.get('max_scrolls', 10)
        
        # Forward the request to the backend
        response = requests.get(
            f"{EXTRACTORT_URL}/extract/hashtag/{hashtag}",
            params={
                'max_tweets': max_tweets,
                'min_tweets': min_tweets,
                'max_scrolls': max_scrolls
            },
            timeout=30
        )
        
        # Return the response from the backend with the same content type
        return response.content, response.status_code, {'Content-Type': response.headers.get('Content-Type')}
            
    except requests.RequestException as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to connect to the ExtractorT service: {str(e)}"
        }), 500

@app.route('/extractT/user/<username>', methods=['GET'])
def extract_user(username):
    """Forward user extraction request to the ExtractorT service."""
    try:
        # Get query parameters
        max_tweets = request.args.get('max_tweets', 30)
        min_tweets = request.args.get('min_tweets', 10)
        max_scrolls = request.args.get('max_scrolls', 10)
        
        # Forward the request to the backend
        response = requests.get(
            f"{EXTRACTORT_URL}/extract/user/{username}",
            params={
                'max_tweets': max_tweets,
                'min_tweets': min_tweets,
                'max_scrolls': max_scrolls
            },
            timeout=30
        )
        
        # Return the response from the backend with the same content type
        return response.content, response.status_code, {'Content-Type': response.headers.get('Content-Type')}
            
    except requests.RequestException as e:
        return jsonify({
            "status": "error",
            "message": f"Failed to connect to the ExtractorT service: {str(e)}"
        }), 500

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint that also checks both backend health."""
    # Check first backend health
    try:
        start_time = time.time()
        backend_health = requests.get(f"{TWEET_EXTRACTOR_URL}/health", timeout=5)
        response_time = time.time() - start_time
        
        backend_status = backend_health.json() if backend_health.status_code == 200 else {
            "status": "error",
            "message": f"Backend returned status code {backend_health.status_code}"
        }
        backend_status["response_time"] = round(response_time * 1000, 2)  # ms
    except requests.RequestException as e:
        backend_status = {
            "status": "error",
            "message": f"Failed to connect to backend: {str(e)}"
        }
    
    # Check second backend (ExtractorT) health
    try:
        start_time = time.time()
        extractort_health = requests.get(f"{EXTRACTORT_URL}/health", timeout=5)
        response_time = time.time() - start_time
        
        extractort_status = extractort_health.json() if extractort_health.status_code == 200 else {
            "status": "error",
            "message": f"ExtractorT returned status code {extractort_health.status_code}"
        }
        extractort_status["response_time"] = round(response_time * 1000, 2)  # ms
    except requests.RequestException as e:
        extractort_status = {
            "status": "error",
            "message": f"Failed to connect to ExtractorT: {str(e)}"
        }
    
    # Frontend (this service) health status
    proxy_status = {
        "status": "healthy",
        "service": "tweet-extractor-proxy",
        "timestamp": time.strftime("%Y-%m-%d %H:%M:%S")
    }
    
    return jsonify({
        "proxy": proxy_status,
        "backend": backend_status,
        "extractorT": extractort_status
    })

if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
