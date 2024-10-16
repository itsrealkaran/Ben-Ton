# Ben-Ton

**Ben-Ton** is a retro-themed First Person Shooter (FPS) game built using Python. It leverages the Aptos Python SDK to manage player scores and maintain a leaderboard directly on the blockchain. By integrating blockchain technology, Ben-Ton ensures secure, transparent, and tamper-proof score tracking and leaderboard management.

## Table of Contents

- [Features](#features)
- [Demo](#demo)
- [Getting Started](#getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#usage)
  - [Running the Game](#running-the-game)
  - [Connecting Wallet](#connecting-wallet)
  - [Testing Smart Contract](#testing-smart-contract)
- [Smart Contract](#smart-contract)
  - [Overview](#overview)
  - [Deployment](#deployment)
- [Contributing](#contributing)
- [License](#license)
- [Acknowledgements](#acknowledgements)
- [Contact](#contact)

## Features

- **Retro FPS Gameplay:** Experience classic first-person shooter mechanics with a nostalgic retro aesthetic.
- **Blockchain Integration:** Utilize the Aptos blockchain to securely manage and store player scores.
- **On-Chain Leaderboard:** View and compete on a transparent, tamper-proof leaderboard maintained on-chain.
- **Custodial Wallet Management:** The game manages player wallets, simplifying the blockchain interaction process.
- **Asynchronous Operations:** Smooth gameplay experience with asynchronous blockchain interactions.
- **Extensible Architecture:** Modular codebase allowing for easy feature additions and modifications.

## Getting Started

Follow these instructions to set up and run Ben-Ton on your local machine for development and testing purposes.

### Prerequisites

- **Python 3.10 or later:** Ensure you have Python installed. You can download it from [Python's official website](https://www.python.org/downloads/).
- **Pygame:** Used for game development.
- **Aptos Developer Account:** Required to interact with the Aptos blockchain and deploy smart contracts.
- **Aptos CLI:** For managing and deploying smart contracts. [Installation Guide](https://aptos.dev/aptos-core/cli.html)
- **Node.js and npm (optional):** If you plan to extend the project with frontend components.

### Installation

1. **Clone the Repository**

   ```bash
   git clone https://github.com/itsrealkaran/ben-ton.git
   cd ben-ton
   ```

2. **Create a Virtual Environment**

   It's recommended to use a virtual environment to manage dependencies.

   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install Dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   *If `requirements.txt` is not available, install dependencies manually:*

   ```bash
   pip install pygame aptos-sdk
   ```

4. **Set Up Environment Variables**

   Create a `.env` file in the project root directory and add your Aptos node and faucet URLs if different from the defaults.

   ```env
   NODE_URL=https://fullnode.devnet.aptoslabs.com/v1
   FAUCET_URL=https://faucet.devnet.aptoslabs.com
   CONTRACT_ADDRESS=0xc9e9c2805af30b768fd1ac9d4b37ac114a3f16c675abdfc985c44ac5061fcd20
   ```

### Configuration

1. **Deploy the Smart Contract**

   Ensure that the `leader.move` smart contract is deployed on the Aptos DevNet and note the contract address.

   ```bash
   aptos move compile
   aptos move publish --package-dir path/to/contract --named-address benton=YOUR_ADDRESS
   ```

   Replace `YOUR_ADDRESS` with your Aptos address obtained from the Aptos CLI.

2. **Update Configuration**

   Update the `contract_address` in `main.py` if it's different from the default provided.

   ```python
   self.contract_address = "0xc9e9c2805af30b768fd1ac9d4b37ac114a3f16c675abdfc985c44ac5061fcd20"
   ```

## Usage

### Running the Game

1. **Activate the Virtual Environment**

   ```bash
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

2. **Run the Game**

   ```bash
   python main.py
   ```

## Smart Contract

### Overview

The smart contract is written in Aptos Move and manages the leaderboard functionality. It handles account initialization, score updates, and fetching leaderboard data.

### Deployment

1. **Compile the Smart Contract**

   ```bash
   aptos move compile
   ```

2. **Publish the Smart Contract**

   ```bash
   aptos move publish --package-dir path/to/contract --named-address benton=YOUR_ADDRESS
   ```

   Replace `YOUR_ADDRESS` with your Aptos address.

3. **Verify Deployment**

   Ensure that the contract is successfully deployed by checking the Aptos DevNet explorer.

## Contributing

Contributions are welcome! Please follow these steps:

1. **Fork the Repository**
2. **Create a Feature Branch**

   ```bash
   git checkout -b feature/YourFeature
   ```

3. **Commit Your Changes**

   ```bash
   git commit -m "Add some feature"
   ```

4. **Push to the Branch**

   ```bash
   git push origin feature/YourFeature
   ```

5. **Open a Pull Request**

## License

This project is licensed under the [MIT License](LICENSE).
