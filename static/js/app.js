document.addEventListener("DOMContentLoaded", () => {
    console.log("App loaded successfully!");

    const MESSAGES = {
        REGISTER_SUCCESS: "Voter registered successfully!",
        REGISTER_FAIL: "Failed to register voter.",
        INVALID_INPUT: "All fields are required!",
        PASSWORD_LENGTH: "Password must be at least 8 characters long.",
        VOTE_SUCCESS: "Vote cast successfully!",
        TOKEN_GENERATED: "JWT Token generated successfully!",
        BLOCK_MINED: "New block mined!",
        FETCH_ERROR: "Failed to fetch data. Please try again.",
    };

    // Utility function for API calls
    async function apiFetch(endpoint, options = {}) {
        try {
            const response = await fetch(endpoint, options);
            if (!response.ok) {
                const errorData = await response.json();
                console.error(`API Error: ${errorData.message || "Unknown error"}`);
                throw new Error(`HTTP error! status: ${response.status}`);
            }
            return await response.json();
        } catch (error) {
            console.error(`Error in API call to ${endpoint}:`, error);
            throw error;
        }
    }


    // Display messages on the UI
    function displayMessage(message, sectionId) {
        const section = document.getElementById(sectionId);
        if (section) {
            section.textContent = message;
            section.style.display = "block";
        } else {
            console.error(`Section with ID ${sectionId} not found.`);
        }
    }


    // Add event listeners to buttons
    document.querySelectorAll(".btn").forEach(button => {
        button.addEventListener("click", handleButtonClick);
    });

    // Button click handler
    async function handleButtonClick(event) {
        const action = event.currentTarget.textContent.trim();
        console.log("Button clicked: ", action);

        try {
            switch (action) {
                case "Register":
                    await registerVoter();
                    break;
                case "Vote Now":
                    console.log("Calling showVoteChoiceSection");
                    showVoteChoiceSection();
                    break;
                case "Mine":
                    await mineBlock();
                    break;
                case "Generate Token":
                    await generateToken();
                    break;
                case "View Blockchain":
                    await viewBlockchain();
                    break;
                case "View Results":
                    await viewResults();
                    break;
                default:
                    console.error("Unknown action: ", action);
            }
        } catch (error) {
            alert(MESSAGES.FETCH_ERROR);
        }
    }

    // Register a voter
    async function registerVoter() {
        const voterId = prompt("Enter your voter ID:");
        const password = prompt("Enter a secure password (at least 8 characters):");

        if (!voterId || !password) {
            alert(MESSAGES.INVALID_INPUT);
            return;
        }

        if (password.length < 8) {
            alert(MESSAGES.PASSWORD_LENGTH);
            return;
        }

        try {
            const data = await apiFetch("/submit_voter", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ voter_id: voterId, password: password })
            });

            alert(data.message || MESSAGES.REGISTER_SUCCESS);
            displayMessage(data.message, "resultSection");
        } catch (error) {
            alert(MESSAGES.REGISTER_FAIL);
        }
    }

    // Show the vote choice section
    function showVoteChoiceSection() {
        console.log("Inside showVoteChoiceSection");
        let voteChoiceSection = document.getElementById("voteChoiceSection");
    
        if (!voteChoiceSection) {
            console.log("Creating vote choice section");
            voteChoiceSection = document.createElement("div");
            voteChoiceSection.id = "voteChoiceSection";
    
            const label = document.createElement("label");
            label.textContent = "Choose your candidate:";
            label.setAttribute("for", "voteChoice");
    
            const select = document.createElement("select");
            select.id = "voteChoice";
            const candidates = ["Candidate 1", "Candidate 2", "Candidate 3"];
            candidates.forEach((candidate) => {
                const option = document.createElement("option");
                option.value = candidate;
                option.textContent = candidate;
                select.appendChild(option);
            });
    
            const submitButton = document.createElement("button");
            submitButton.id = "submitVoteButton";
            submitButton.textContent = "Submit Vote";
            submitButton.style.marginTop = "10px";
    
            voteChoiceSection.appendChild(label);
            voteChoiceSection.appendChild(select);
            voteChoiceSection.appendChild(submitButton);
            document.body.appendChild(voteChoiceSection);
        } else {
            console.log("Vote choice section already exists");
            document.getElementById("voteChoice").selectedIndex = 0;
            voteChoiceSection.style.display = "block";
        }
    
        // Always rebind the click event to ensure proper behavior
        const submitButton = document.getElementById("submitVoteButton");
        if (submitButton) {
            submitButton.addEventListener("click", castVote);
        }
    }
    
   
    

    // Cast a vote
    async function castVote() {
        console.log("castVote function called");

        const token = prompt("Enter your JWT token (generated during registration):");
        const voterId = prompt("Enter your voter ID:");
        const password = prompt("Enter your password:");
        const voteChoice = document.getElementById("voteChoice")?.value;

        console.log("Voting with: ", { token, voterId, password, voteChoice });

        if (!voterId || !password || !voteChoice) {
            alert(MESSAGES.INVALID_INPUT);
            return;
        }

        try {
            const payload = {
                voter_id: voterId,
                password: password,
                vote_choice: voteChoice.trim(),
            };

            const options = {
                method: "POST",
                headers: {
                    "Content-Type": "application/json",
                    "Authorization": `Bearer ${token || ""}`,
                },
                body: JSON.stringify(payload),
            };

            console.log("API Request Options: ", options);
            const data = await apiFetch("/vote", options);

            console.log("API Response: ", data);

            alert(data.message || MESSAGES.VOTE_SUCCESS);
            displayMessage(data.message, "resultSection");
            hideVoteChoiceSection();
        } catch (error) {
            console.error("Error casting vote: ", error);
            alert(MESSAGES.FETCH_ERROR);
        }
    }

    // Hide vote choice section
    function hideVoteChoiceSection() {
        const voteChoiceSection = document.getElementById("voteChoiceSection");
        if (voteChoiceSection) voteChoiceSection.style.display = "none";
    }

    // Mine a block
    async function mineBlock() {
        try {
            const data = await apiFetch("/mine");
            if (data.index) {
                displayMessage(`New block mined! Block index: ${data.index}`, "resultSection");
            }
        } catch (error) {
            displayMessage(MESSAGES.FETCH_ERROR, "resultSection");
        }
    }

    // Generate a JWT token
    async function generateToken() {
        const voterId = prompt("Enter your voter ID:");

        if (!voterId) {
            alert(MESSAGES.INVALID_INPUT);
            return;
        }

        try {
            const data = await apiFetch("/generate_token", {
                method: "POST",
                headers: { "Content-Type": "application/json" },
                body: JSON.stringify({ voter_id: voterId })
            });

            if (data.token) {
                alert(`${MESSAGES.TOKEN_GENERATED} Token: ${data.token}`);
                displayMessage(`${MESSAGES.TOKEN_GENERATED} Token: ${data.token}`, "resultSection");
                displayToken(data.token);
            } else {
                alert(MESSAGES.FETCH_ERROR);
            }
        } catch (error) {
            alert(MESSAGES.FETCH_ERROR);
        }
    }

    // View the Blockchain
    async function viewBlockchain() {
        try {
            const data = await apiFetch("/chain");
            if (data.chain) {
                const chainContent = document.getElementById("chainContent");
                chainContent.textContent = JSON.stringify(data.chain, null, 2);
                document.getElementById("chainSection").style.display = "block";
            } else {
                alert(MESSAGES.FETCH_ERROR);
            }
        } catch (error) {
            alert(MESSAGES.FETCH_ERROR);
        }
    }

    // View the Results
    async function viewResults() {
        try {
            const response = await fetch("/results"); // Fetch the results from the server
            if (!response.ok) {
                throw new Error(`HTTP error! status: ${response.status}`);
            }
    
            const data = await response.json(); // Parse the JSON response
            console.log("Received results data:", data);  // Log the complete data
    
            const resultSection = document.getElementById("resultSection");
    
            // Clear previous results
            resultSection.innerHTML = '';
    
            if (data.results && Object.keys(data.results).length > 0) {
                console.log("Results found:", data.results); // Log the results specifically
    
                const formattedResults = Object.entries(data.results)
                    .map(([candidate, votes]) => `<p>${candidate}: ${votes} votes</p>`)
                    .join("");
    
                resultSection.innerHTML = `
                    <h2>Election Results</h2>
                    ${formattedResults}
                `;
            } else {
                resultSection.innerHTML = `
                    <h2>Election Results</h2>
                    <p>No votes have been cast yet or the results are still being calculated.</p>
                `;
            }
    
            resultSection.style.display = "block"; // Ensure the result section is visible
        } catch (error) {
            console.error("Error fetching results:", error);
            alert("Failed to fetch results. Please try again later.");
        }
    }
    

    // Display the JWT token on the page
    function displayToken(token) {
        const tokenSection = document.getElementById("tokenSection");
        const jwtTokenSpan = document.getElementById("jwtToken");
        jwtTokenSpan.textContent = token;
        tokenSection.style.display = "block";
    }
});
