from genlayer_py import create_client
from genlayer_py.chains import localnet

CONTRACT_ADDRESS = "0x8A74fCD1A590212625a5Fd7937ceeFdca16066E5"
AGENT = "0x69d353B9178e357Ce28FD1678486A7BcCf2d65C8"


def test_open_and_evaluate_case():
    client = create_client(chain=localnet)

    tx = client.write_contract(
        address=CONTRACT_ADDRESS,
        function_name="open_case",
        args=[AGENT, "Agent repeatedly submitted plagiarized deliverables that failed originality checks."],
    )
    receipt = client.wait_for_transaction_receipt(hash=tx)
    assert receipt is not None


def test_case_not_found():
    client = create_client(chain=localnet)
    result = client.read_contract(address=CONTRACT_ADDRESS, function_name="get_case", args=[999999])
    assert result == "NOT_FOUND"
