contract = ADGToken.deploy("adg", "adg", {"from":accounts[0]})

tx = contract.addItem(accounts[1].address, 450, "Great stuff", 0)
item_id_1 = tx.return_value
print(f"Returned value {item_id_1}")
tx.info()

contract.setWantToBuyForUser(accounts[2].address, item_id_1).info()

accounts[2].transfer(contract.address, "0.000001 ether").info()
#                                        buyer           item_id
contract.tryToConfirmByTimePassed(accounts[2].address, item_id_1).info()
chain.sleep(301)
contract.tryToConfirmByTimePassed(accounts[2].address, item_id_1).info()