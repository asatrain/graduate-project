require("@nomicfoundation/hardhat-toolbox");
require("@nomiclabs/hardhat-etherscan");
require("dotenv").config();

const { 
  GOERLI_API_URL, SEPOLIA_API_URL, MUMBAI_API_URL, LOCAL_API_URL,
  GOERLI_PRIVATE_KEY_0, GOERLI_PRIVATE_KEY_1, SEPOLIA_PRIVATE_KEY_0, SEPOLIA_PRIVATE_KEY_1, MUMBAI_PRIVATE_KEY_0, MUMBAI_PRIVATE_KEY_1, LOCAL_PRIVATE_KEY_0, LOCAL_PRIVATE_KEY_1,
  ETHERSCAN_API_KEY, POLYGONSCAN_API_KEY
} = process.env;

/** @type import('hardhat/config').HardhatUserConfig */
module.exports = {
  solidity: "0.8.18",
  networks: {
    goerli: {
      url: GOERLI_API_URL,
      accounts: [
        `0x${GOERLI_PRIVATE_KEY_0}`,
        `0x${GOERLI_PRIVATE_KEY_1}`
      ]
    },
    sepolia: {
      url: SEPOLIA_API_URL,
      accounts: [
        `0x${SEPOLIA_PRIVATE_KEY_0}`,
        `0x${SEPOLIA_PRIVATE_KEY_1}`
      ]
    },
    mumbai: {
      url: MUMBAI_API_URL,
      accounts: [
        `0x${MUMBAI_PRIVATE_KEY_0}`,
        `0x${MUMBAI_PRIVATE_KEY_1}`
      ]
    },


  },
  etherscan: {
    // Your API key for Etherscan
    // Obtain one at https://etherscan.io/
    apiKey: POLYGONSCAN_API_KEY
  },
};