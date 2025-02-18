from flask import Flask, jsonify, request, render_template
import hashlib
import time
import json
import jwt
import datetime
import logging
from functools import wraps
from werkzeug.security import generate_password_hash, check_password_hash
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask import send_file
import os

# Setup
SECRET_KEY = os.getenv('SECRET_KEY', 'your_secret_key')  # Use environment variable for production

def generate_token(voter_id):
    return jwt.encode(
        {'voter_id': voter_id, 'exp': datetime.datetime.now(datetime.timezone.utc) + datetime.timedelta(hours=1)},
        SECRET_KEY,
        algorithm='HS256'
    )

# Simulating a database for voter credentials (passwords), replace this with an actual database in production
voter_passwords = {}

def authenticate_token(f):
    @wraps(f)
    def wrapper(*args, **kwargs):
        token = request.headers.get('Authorization')

        if not token:
            return jsonify({'message': 'Token is missing!'}), 401

        try:
            # Extract the token (remove "Bearer " prefix if present)
            token = token.split()[1] if token.startswith("Bearer ") else token

            # Decode the token with signature verification
            decoded_token = jwt.decode(token, SECRET_KEY, algorithms=['HS256'])
            print(f"Decoded token: {decoded_token}")
            
            # Check token expiration
            expiration_time = datetime.datetime.fromtimestamp(decoded_token['exp'], tz=datetime.timezone.utc)
            if expiration_time < datetime.datetime.now(tz=datetime.timezone.utc):
             return jsonify({'message': 'Token has expired!'}), 403
        except jwt.ExpiredSignatureError:
            return jsonify({'message': 'Token has expired!'}), 403
        except jwt.InvalidTokenError:
            return jsonify({'message': 'Invalid token!'}), 403
        
        # Add decoded token info to request context
        request.voter_id = decoded_token['voter_id']

        return f(*args, **kwargs)

    return wrapper

# Blockchain Class
class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_votes = []
        self.voters = set()
        self.candidates = ['Candidate 1', 'Candidate 2', 'Candidate 3']
        self.new_block(previous_hash='1', proof=100)

    def new_block(self, proof, previous_hash=None):
        block = {
            'index': len(self.chain) + 1,
            'timestamp': time.time(),
            'votes': self.current_votes,
            'proof': proof,
            'previous_hash': previous_hash or self.hash(self.chain[-1]),
        }
        self.current_votes = []
        self.chain.append(block)
        return block

    def new_vote(self, voter_id, vote_choice):
       normalized_choice = vote_choice.strip().title()
       if normalized_choice not in self.candidates:
        print(f"Invalid vote choice: {normalized_choice}")
        return False  # Invalid vote choice
       if voter_id in self.voters:
        print(f"Voter {voter_id} has already voted.")
        return False  # Voter has already voted

       print(f"Recording vote for {voter_id}: {normalized_choice}")
       self.voters.add(voter_id)
       self.current_votes.append({
           'voter_id': voter_id,
           'vote_choice': normalized_choice
       })
       return len(self.chain) + 1



    def is_chain_valid(self):
        for i in range(1, len(self.chain)):
            current_block = self.chain[i]
            previous_block = self.chain[i - 1]

            if current_block['previous_hash'] != self.hash(previous_block):
                return False

            if not self.valid_proof(previous_block['proof'], current_block['proof']):
                return False
        return True

    @staticmethod
    def hash(block):
        block_string = json.dumps(block, sort_keys=True).encode()
        return hashlib.sha256(block_string).hexdigest()

    @property
    def last_block(self):
        return self.chain[-1]

    def proof_of_work(self, last_proof):
        proof = 0
        while self.valid_proof(last_proof, proof) is False:
            proof += 1
        return proof

    @staticmethod
    def valid_proof(last_proof, proof):
        guess = f'{last_proof}{proof}'.encode()
        guess_hash = hashlib.sha256(guess).hexdigest()
        return guess_hash[:4] == '0000'

# Initialize Flask app
app = Flask(__name__, static_folder='static')
limiter = Limiter(
    key_func=get_remote_address,
    storage_uri='memory://'
)
limiter.init_app(app)

# Configure logging
logging.basicConfig(level=logging.INFO)

# Initialize Blockchain
blockchain = Blockchain()

@app.route('/favicon.ico')
def favicon():
    return send_file('favicon.png', mimetype='image/png')

@app.route('/')
def index():
    print("Index function called")
    try:
        return render_template('index2.html', static_folder='static')
    except Exception as e:
        print(f"Error rendering index2.html: {e}")
        return "Error rendering index2.html"

@app.route('/home', methods=['GET'])
def home():
    return jsonify({
        'message': 'Welcome to the Student Council Blockchain Voting System!',
        'endpoints': {
            '/submit_voter': 'Submit a new voter (POST)',
            '/vote': 'Submit a vote (POST)',
            '/mine': 'Mine a new block (GET)',
            '/chain': 'View the blockchain (GET)',
            '/results': 'View the election results (GET)',
            '/generate_token': 'Generate JWT token for voting (POST)',
            '/refresh_token': 'Refresh JWT token (POST)'
        }
    }), 200

@app.route('/submit_voter', methods=['POST'])
@limiter.limit("5 per minute")
def submit_voter():
    data = request.get_json()
    voter_id = data.get('voter_id')
    password = data.get('password')

    if not voter_id or not password:
        return jsonify({'message': 'Missing voter_id or password'}), 400

    if len(password) < 8:
        return jsonify({'message': 'Password must be at least 8 characters long'}), 400

    # Hash the password and store it
    voter_passwords[voter_id] = generate_password_hash(password)

    logging.info(f'Voter registered: {voter_id}')
    return jsonify({'message': 'Voter registered successfully.'}), 200

@app.route('/vote', methods=['POST'])
@limiter.limit("5 per minute")
@authenticate_token
def vote():
    data = request.get_json()
    voter_id = data.get('voter_id')
    vote_choice = data.get('vote_choice')
    password = data.get('password')

    if not voter_id or not vote_choice or not password:
        return jsonify({'message': 'Missing voter_id, vote_choice, or password'}), 400

    if voter_id not in voter_passwords or not check_password_hash(voter_passwords[voter_id], password):
        return jsonify({'message': 'Invalid voter ID or password!'}), 400

    if not blockchain.new_vote(voter_id, vote_choice):
        return jsonify({'message': 'Voter has already voted or invalid vote choice!'}), 400

    logging.info(f'Vote received: {voter_id} for {vote_choice}')
    return jsonify({'message': f'Vote for {vote_choice} by voter {voter_id} registered successfully.'}), 200

@app.route('/generate_token', methods=['POST'])
def generate_voter_token():
    data = request.get_json()
    voter_id = data.get('voter_id')
    if not voter_id:
        return jsonify({'message': 'voter_id is required'}), 400
    token = generate_token(voter_id)
    return jsonify({'token': token}), 200

@app.route('/refresh_token', methods=['POST'])
@authenticate_token
def refresh_token():
    data = request.get_json()
    voter_id = data.get('voter_id')
    if not voter_id:
        return jsonify({'message': 'voter_id is required'}), 400
    token = generate_token(voter_id)
    return jsonify({'token': token}), 200

@app.route('/mine', methods=['GET'])
def mine():
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    previous_hash = blockchain.hash(last_block)
    block = blockchain.new_block(proof, previous_hash)

    return jsonify({
        'message': 'New Block Mined!',
        'index': block['index'],
        'timestamp': block['timestamp'],
        'votes': block['votes'],
        'proof': block['proof'],
        'previous_hash': block['previous_hash']
    }), 200

@app.route('/chain', methods=['GET'])
def full_chain():
    # Check if the blockchain is valid
    chain_valid = blockchain.is_chain_valid()

    # Prepare the response with blockchain data and validity status
    response_data = {
        'chain': blockchain.chain,
        'length': len(blockchain.chain),
        'is_valid': chain_valid
    }

    # Return the JSON response
    return jsonify(response_data), 200

@app.route('/results', methods=['GET'])
def election_results():
    vote_counts = {candidate: 0 for candidate in blockchain.candidates}
    
    # Debug log
    print("Blockchain structure:", blockchain.chain)

    for block in blockchain.chain:
        print(f"Processing block {block['index']}")
        for vote in block.get('votes', []):
            print(f"Processing vote: {vote}")
            vote_counts[vote['vote_choice']] += 1
    
    print("Final vote counts:", vote_counts)
    return jsonify({'election_results': vote_counts}), 200


@app.errorhandler(Exception)
def handle_exception(e):
    logging.error(f'An error occurred: {str(e)}')
    return jsonify({'message': 'An unexpected error occurred.'}), 500

if __name__ == '__main__':
    logging.info("Starting Flask app...")
    app.run(debug=False, host='127.0.0.1', port=8080)
