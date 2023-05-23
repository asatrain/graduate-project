async function main() {
    const [deployer] = await ethers.getSigners();
    console.log("Deploying contracts with the account:", deployer.address);
    console.log("Account balance:", (await deployer.getBalance()).toString());
    const Token = await ethers.getContractFactory("ADGToken");
    const token = await Token.deploy("Art de Grace", "ADG");
    console.log("Token address:", token.address);
  }
  main()
    .then(() => process.exit(0))
    .catch((error) => {
      console.error(error);
      process.exit(1);
    });