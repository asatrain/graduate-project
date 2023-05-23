import argparse
from connectors import ConnectorADG
import connectors

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description='Local or Testnet')
    parser.add_argument('--net', default="sepolia")
    args = parser.parse_args()
    net = args.net
    
    connector = ConnectorADG(net=net)
    # item_id = int(connectors.generate_random_item_id(), 0)
    item_id = 36523823523946859337227252947287996457583359493841478032303213246476261046098
    # connector.add_item("0x71db36a96E96d88d3beeCA009bee87bEE201Ce8b", 45000000000000, "Great stuff", item_id)
    # connector.want_to_buy("0x726ab7CB9Ad545D27C7EBe06C9928a079e156A91", item_id)
    #
    # connector.openDispute("0x71db36a96E96d88d3beeCA009bee87bEE201Ce8b", item_id)
    # connector.resolveDisputeForSeller("0x71db36a96E96d88d3beeCA009bee87bEE201Ce8b", item_id)



    # connector.tryToConfirm("0x71db36a96E96d88d3beeCA009bee87bEE201Ce8b","0x726ab7CB9Ad545D27C7EBe06C9928a079e156A91",101183841031019182202565154070630143999802150143861267697552987922200091485445)
    # print("ADD ITEM")
    # item_id = connector.add_item("0x1CBd3b2770909D4e10f157cABC84C7264073C9Ec", 433, "Super KICKS")
    # print(item_id)
    # connector.openDispute("", 2502703511121)
    # connector.openDispute("0x726ab7CB9Ad545D27C7EBe06C9928a079e156A91",101183841031019182202565154070630143999802150143861267697552987922200091485445)
    
    '''
    print("ADD ITEM")
    print(connector.add_item("0x1CBd3b2770909D4e10f157cABC84C7264073C9Ec", 433, "Super KICKS", 666))
    print("GET ITEM")
    print(connector.get_item(666))
    print("WANT TO BUY")
    print(connector.want_to_buy("0x726ab7CB9Ad545D27C7EBe06C9928a079e156A91", 666))
    '''
    # print(connector.get_order("0x71db36a96E96d88d3beeCA009bee87bEE201Ce8b", 666))
    # print(connector.checkPaid("0x726ab7CB9Ad545D27C7EBe06C9928a079e156A91", 666))
    # print(connector.getDispute("0x726ab7CB9Ad545D27C7EBe06C9928a079e156A91", 666))
    # print(connector.add_item("0x1CBd3b2770909D4e10f157cABC84C7264073C9Ec", 100, "Bruh kikcs"))