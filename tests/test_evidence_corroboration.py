from genlayer_py import create_client
from genlayer_py.chains import localnet

CONTRACT_ADDRESS = "0x55626a15C46Cbba6BfD3F1DBFe9Df4F30c0aA035"
AGENT = "0x69d353B9178e357Ce28FD1678486A7BcCf2d65C8"


def test_submit_and_evaluate_soft():
    client = create_client(chain=localnet)

    tx = client.write_contract(
        address=CONTRACT_ADDRESS,
        function_name="submit_evidence",
        args=[AGENT, "Deployment log shows contract verified with matching bytecode hash."],
    )
    receipt = client.wait_for_transaction_receipt(hash=tx)
    assert receipt is not None


def test_evidence_not_found():
    client = create_client(chain=localnet)
    result = client.read_contract(address=CONTRACT_ADDRESS, function_name="get_evidence", args=[999999])
    assert result == "NOT_FOUND"
