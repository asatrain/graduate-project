//SPDX-License-Identifier: Unlicense
pragma solidity >=0.8.18; 

import "@openzeppelin/contracts/token/ERC721/ERC721.sol";
import "@openzeppelin/contracts/token/ERC721/extensions/ERC721URIStorage.sol";
import "@openzeppelin/contracts/utils/Base64.sol";
import "@openzeppelin/contracts/utils/Strings.sol";


contract ADGToken is ERC721, ERC721URIStorage {

    modifier OnlyOwner {
		require(msg.sender == owner);
		_;
	}

    struct Item {
        address seller;
        uint256 price;
        string nameOfItem;
        bool exists;
        uint256 auctionDuration;
        uint256 creationTimestamp;
        address lastBetAddress;
        uint256 lastBetValue;
        string imageURI;
    }

    struct Want {
        uint256 itemId;
        bool exists;
    }

    enum OrderStatus{ PENDING, BUYER_CONFIRMED, DISPUTE_OPENED, RESOLVED_FOR_BUYER }

    struct Order {
        address buyer;
        uint256 purchaseTimestamp;
        OrderStatus status;
        bool exists;
    }

    function getBalance() public view OnlyOwner returns (uint256) {
        return address(this).balance;
    }


    uint256 public itemCounter;
    address public owner;
    uint256 threshInSeconds;

    constructor(
        string memory name,
        string memory symbol
    ) ERC721(name, symbol) {
        owner = msg.sender;
        itemCounter = 0;
        // threshInSeconds = 2419200; // 28 days
        threshInSeconds = 600;  // 5 minutes
    }


    mapping(address => uint256) balances;
    mapping(address => Want) wantToBuy;
    mapping(uint256 => Item) items;
    //      itemId  
    mapping(uint256 => Order) orders;

    function getItem(uint256 itemId) public view OnlyOwner returns (address, uint256, string memory, bool, uint256, uint256, address, uint256) {
        Item memory curItem = items[itemId];
        return (curItem.seller, curItem.price, curItem.nameOfItem, curItem.exists, curItem.auctionDuration, curItem.creationTimestamp, curItem.lastBetAddress, curItem.lastBetValue);
    }

    function getOrder(uint256 itemId) public view OnlyOwner returns (address, uint256, OrderStatus, bool, uint256) {
        Order memory curOrder = orders[itemId];
        //                                                                                                 time passed
        return (curOrder.buyer, curOrder.purchaseTimestamp, curOrder.status, curOrder.exists, block.timestamp - curOrder.purchaseTimestamp);
    }


    event AddedItem(uint256 id, address seller, uint price, string nameOfItem, bool exists, uint256 auctionDuration, uint256 creationTimestamp, address lastBetAddress, uint256 lastBetValue, string imageURI);
    event DuplicateItem(uint256);

    function addItem(address seller, uint price, string memory nameOfItem, uint256 auctionDuration, string memory imageURI) public OnlyOwner returns (uint256) {
        itemCounter += 1;
        //                        seller  price  nameOfItem exists auctionDuration  creationTimestamp lastBetAddress lastBetValue imeageURI
        items[itemCounter] = Item(seller, price, nameOfItem, true, auctionDuration, block.timestamp, address(0), 0, imageURI);
        emit AddedItem(itemCounter, seller, price, nameOfItem, true, auctionDuration, block.timestamp, address(0), 0, imageURI);

        return itemCounter;
    }

    event SetWantToBuy(address buyer, uint256 itemId);

    function setWantToBuyForUser(address buyer, uint256 itemId) public OnlyOwner {
        require(items[itemId].exists, "This item doesn't exist");
        wantToBuy[buyer] = Want(itemId, true);
        emit SetWantToBuy(buyer, itemId);
    }

    event ItemNotFound(uint itemId);
    event ItemRemoved(uint itemId);

    function removeItem(uint itemId) public OnlyOwner {
        require(items[itemId].exists, "This item doesn't exist");
        items[itemId].exists = false;
        emit ItemRemoved(itemId);
    }

    event RefundMade(address refundedAddress, uint256 amount);

    function makeRefund(address toRefund, uint256 refundValue) private {
        payable(toRefund).transfer(refundValue);
        emit RefundMade(toRefund, refundValue);
    }

    event OrderIsPending(address buyer, uint256 itemId);
    event DeletedItem(uint256 itemId);

    function createOrder(address buyer, uint256 itemId) private {
        orders[itemId] = Order(buyer, block.timestamp, OrderStatus.PENDING, true);
        emit OrderIsPending(msg.sender, itemId);
        items[itemId].exists = false;
        emit DeletedItem(itemId);
    }

    event WantToBuyWasntSet(address sender);
    event AuctionFinished(uint256 itemId, address winner);
    event NotEnoughFundsSent(address sender, uint256 itemId);
    event PartialRefundMade(address refundedAddress, uint256 amount);
    event NewBet(address betFrom, uint256 amount);

    receive() external payable {
        
        if ( (!wantToBuy[msg.sender].exists) || (!items[wantToBuy[msg.sender].itemId].exists) ) {
            emit WantToBuyWasntSet(msg.sender);
            makeRefund(msg.sender, msg.value);
            return;
        }

        uint256 itemId = wantToBuy[msg.sender].itemId;

        if (items[itemId].creationTimestamp + items[itemId].auctionDuration <= block.timestamp && items[itemId].lastBetAddress != address(0)) {
            // Auction finished, but Order wasn't created
            //                                      winner
            emit AuctionFinished(itemId, items[itemId].lastBetAddress);
            makeRefund(msg.sender, msg.value);
            return;
        }
        
        if (msg.value < items[itemId].price) {
            emit NotEnoughFundsSent(msg.sender, itemId);
            makeRefund(msg.sender, msg.value);
        } else {
            if (items[itemId].creationTimestamp + items[itemId].auctionDuration <= block.timestamp) {
                // Auction finished, we must refund redundant 
                uint256 diff = msg.value - items[itemId].price;
                if (diff != 0) {
                    payable(msg.sender).transfer(diff);
                    emit PartialRefundMade(msg.sender, diff);
                }
                items[itemId].lastBetValue = items[itemId].price;
                // Auction has finished, we can create Order
                createOrder(msg.sender, itemId);
            } else {
                // Auction hasn't finished, we must set new price (no Order)
                // Last auction participant must be refunded
                makeRefund(items[itemId].lastBetAddress, items[itemId].lastBetValue);
                items[itemId].lastBetValue = msg.value;
                items[itemId].lastBetAddress = msg.sender;
                items[itemId].price = items[itemId].lastBetValue + (items[itemId].lastBetValue / 100) * 10;
                emit NewBet(items[itemId].lastBetAddress, items[itemId].lastBetValue);
            }
        }
    }


    event NoBetOnAuction(uint256 itemId);

    function createFinishedAuctionOrder(uint256 itemId) OnlyOwner() public {
        require(items[itemId].exists, "Item doesn't exist");
        require(items[itemId].creationTimestamp + items[itemId].auctionDuration <= block.timestamp, "Auction must be finished");
        if (items[itemId].lastBetAddress != address(0)) {
            createOrder(items[itemId].lastBetAddress, itemId);
        } else {
            emit NoBetOnAuction(itemId);
        }
    }


    event SellerPaid(address seller, uint256 price);
    
    function paySeller(address seller, uint256 value) private {
        payable(seller).transfer(value);
        emit SellerPaid(seller, value);
    }


    function successfulOrder(address buyer, uint256 itemId) private {
        orders[itemId].status = OrderStatus.BUYER_CONFIRMED;
        paySeller(items[itemId].seller, items[itemId].lastBetValue);
        mintNft(buyer, itemId);
    }


    function tryToConfirmByTimePassed(uint256 itemId) public {
        Order memory curOrder = orders[itemId];
        require(curOrder.exists, "Order doesn't exist");
        require(curOrder.status == OrderStatus.PENDING, "Order status is not PENDING!");
        require(curOrder.purchaseTimestamp + threshInSeconds <= block.timestamp, "Not enough time has passed to confirm this order!");
        successfulOrder(curOrder.buyer, itemId);
    }


    event DisputeOpened(address buyer, uint256 itemId);

    function openDispute(uint256 itemId) public OnlyOwner {
        Order memory curOrder = orders[itemId];
        require(curOrder.exists, "Order doesn't exist");
        // require(msg.sender == owner || msg.sender == curOrder.buyer, "Only admin or buyer can open dispute");
        require(curOrder.status == OrderStatus.PENDING, "Order status is not PENDING!");
        require(curOrder.purchaseTimestamp + threshInSeconds > block.timestamp, "You can't open dispute after 28 days!");
        orders[itemId].status = OrderStatus.DISPUTE_OPENED;
        emit DisputeOpened(curOrder.buyer, itemId);
    }


    event OrderResolvedToBuyer(address buyer, uint256 itemId, uint256 amount);

    function resolveDisputeForBuyer(uint256 itemId) public OnlyOwner {
        Order memory curOrder = orders[itemId];
        require(curOrder.exists, "Order doesn't exist");
        require(curOrder.status == OrderStatus.DISPUTE_OPENED, "Order status is not DISPUTE_OPENED!");
        orders[itemId].status = OrderStatus.RESOLVED_FOR_BUYER;
        makeRefund(curOrder.buyer, items[itemId].lastBetValue);
        emit OrderResolvedToBuyer(curOrder.buyer, itemId, items[itemId].lastBetValue);
    }


    function resolveDisputeForSeller(uint256 itemId) public OnlyOwner {
        Order memory curOrder = orders[itemId];
        require(curOrder.exists, "Order doesn't exist");
        require(curOrder.status == OrderStatus.DISPUTE_OPENED, "Order status is not DISPUTE_OPENED!");
        orders[itemId].status = OrderStatus.BUYER_CONFIRMED;
        successfulOrder(curOrder.buyer, itemId);
    }


    function tokenURI(uint256 itemId) public view virtual override(ERC721, ERC721URIStorage) returns (string memory) {
        require(
            _exists(itemId),
            "ERC721Metadata: URI query for nonexistent token"
        );
        bytes memory dataURI = abi.encodePacked(
            '{',
                '"name": "ADG #', Strings.toString(itemId), '",',
                '"description": "', items[itemId].nameOfItem, '",',
                '"image": "', items[itemId].imageURI, '",',
                '"attributes": [',
                    '{',
                        '"trait_type": "price",',
                        '"value": ', Strings.toString(items[itemId].price),
                    '}',
                ']',
            '}'
         );

        return string(
            abi.encodePacked(
                "data:application/json;base64,",
                Base64.encode(dataURI)
            )
        );
    }

    function _burn(uint256 tokenId) internal override(ERC721, ERC721URIStorage) {
        super._burn(tokenId);
    }


    event NFTMinted(address buyer, uint256 itemId);

    function mintNft(address to, uint256 itemId) public OnlyOwner {
        _safeMint(to, itemId);
        _setTokenURI(itemId, tokenURI(itemId));
        emit NFTMinted(to, itemId);
    }

}