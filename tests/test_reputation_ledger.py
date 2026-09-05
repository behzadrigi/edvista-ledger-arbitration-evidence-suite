from genlayer_py import create_client
from genlayer_py.chains import localnet

CONTRACT_ADDRESS = "0x4feFdae056a592714FdDbdD98065CfaE80CFB544"
AGENT = "0x69d353B9178e357Ce28FD1678486A7BcCf2d65C8"


def test_register_and_adjust_lifecycle():
    client = create_client(chain=localnet)

    tx = client.write_contract(address=CONTRACT_ADDRESS, function_name="register_agent", args=[AGENT])
    client.wait_for_transaction_receipt(hash=tx)

    assert client.read_contract(address=CONTRACT_ADDRESS, function_name="get_score", args=[AGENT]) == 0
    assert client.read_contract(address=CONTRACT_ADDRESS, function_name="is_registered", args=[AGENT]) is True

    tx = client.write_contract(
        address=CONTRACT_ADDRESS,
        function_name="propose_adjustment",
        args=[AGENT, "INCREASE", 10, "Agent completed 5 verified deliverable evaluations with no disputes."],
    )
    client.wait_for_transaction_receipt(hash=tx)


def test_score_not_found_for_unknown_agent():
    client = create_client(chain=localnet)
    unknown = "0x0000000000000000000000000000000000000001"
    assert client.read_contract(address=CONTRACT_ADDRESS, function_name="get_score", args=[unknown]) == 0
