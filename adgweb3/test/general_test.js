const { expect } = require("chai");

const { loadFixture } = require("@nomicfoundation/hardhat-network-helpers");

describe("ADG Token contract", function () {
  

  async function deployTokenFixture() {
    // Get the ContractFactory and Signers here.
    const Token = await ethers.getContractFactory("ADGToken");
    const [owner, addr1, addr2] = await ethers.getSigners();

    // To deploy our contract, we just have to call Token.deploy() and await
    // its deployed() method, which happens once its transaction has been
    // mined.
    const hardhatToken = await Token.deploy("Art de Grace", "ADG");

    await hardhatToken.deployed();

    // Fixtures can return anything you consider useful for your tests
    return { Token, hardhatToken, owner, addr1, addr2 };
  }

  describe("Deployment", function () {
    it("Should set the right owner", async function () {
      const { hardhatToken, owner } = await loadFixture(deployTokenFixture);
      expect(await hardhatToken.owner()).to.equal(owner.address);
    });

    it("0 tokenCounter", async function () {
      const { hardhatToken, owner } = await loadFixture(deployTokenFixture);
      expect(await hardhatToken.itemCounter()).to.equal(0);
    });
  });

  async function addItem(seller, price, nameOfItem) {
    const { hardhatToken, owner } = await loadFixture(deployTokenFixture);
    addItem()
  }

  describe("Add item", function () {
    it("Should set the right seller of item", async function () {
      const { hardhatToken, owner } = await loadFixture(deployTokenFixture);

    })
  })

});

