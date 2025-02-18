from flask import Flask, jsonify, request, render_template, redirect, url_for
import hashlib
import time
import json

# Blockchain Class
class Blockchain:
    def __init__(self):
        self.chain = []
        self.current_votes = []
        self.voters = set()  # Add a set to track the voters
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
        if voter_id in self.voters:
            return False  # Voter has already voted

        self.voters.add(voter_id)  # Add the voter to the set to prevent further voting
        self.current_votes.append({
            'voter_id': voter_id,
            'vote_choice': vote_choice
        })
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


# Initialize Flask application
app = Flask(__name__)

# Initialize Blockchain
blockchain = Blockchain()


@app.route('/')
def index():
    # Pass a list of candidates to the front-end for the dropdown
    candidates = ["Candidate A", "Candidate B", "Candidate C", "Candidate D"]
    return render_template('index.html', candidates=candidates)



@app.route('/vote', methods=['POST'])
def vote():
    # Get the vote details from the request
    data = request.form
    voter_id = data.get('voter_id')
    vote_choice = data.get('vote_choice')

    if not voter_id or not vote_choice:
        return jsonify({'message': 'Missing voter_id or vote_choice'}), 400

    # Register the vote
    if not blockchain.new_vote(voter_id, vote_choice):
        return render_template('voted.html')

    # Automatically mine a block after the vote
    last_block = blockchain.last_block
    last_proof = last_block['proof']
    proof = blockchain.proof_of_work(last_proof)
    previous_hash = blockchain.hash(last_block)
    blockchain.new_block(proof, previous_hash)

    # Redirect to Thank You page
    return redirect(url_for('thank_you'))


@app.route('/thank_you')
def thank_you():
    return render_template('thankyou.html')


@app.route('/chain', methods=['GET'])
def full_chain():
    return jsonify({
        'chain': blockchain.chain,
        'length': len(blockchain.chain)
    }), 200


if __name__ == '__main__':
    # Run the Flask app
    app.run(debug=True)
