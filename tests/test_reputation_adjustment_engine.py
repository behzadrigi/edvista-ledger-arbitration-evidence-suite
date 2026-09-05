from genlayer_py import create_client
from genlayer_py.chains import localnet

CONTRACT_ADDRESS = "0x95cd5aB72Ef496b2e39130884Dd8Ef779b00e918"
AGENT = "0x69d353B9178e357Ce28FD1678486A7BcCf2d65C8"


def test_record_and_rollback():
    client = create_client(chain=localnet)

    tx = client.write_contract(
        address=CONTRACT_ADDRESS,
        function_name="record_adjustment",
        args=[AGENT, 20, "DECREASE", "ReputationArbitration case 0", 0],
    )
    receipt = client.wait_for_transaction_receipt(hash=tx)
    assert receipt is not None


def test_adjustment_not_found():
    client = create_client(chain=localnet)
    result = client.read_contract(address=CONTRACT_ADDRESS, function_name="get_adjustment", args=[999999])
    assert result == "NOT_FOUND"
