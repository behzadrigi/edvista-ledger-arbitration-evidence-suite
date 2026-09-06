from genlayer_py import create_client
from genlayer_py.chains import localnet

CONTRACT_ADDRESS = "0x238E7eBeF3F90AD36EBB4E4dB599d86bfA4C28A1"
AGENT = "0x69d353B9178e357Ce28FD1678486A7BcCf2d65C8"


def test_open_case_requires_evidence_url():
    client = create_client(chain=localnet)
    tx = client.write_contract(
        address=CONTRACT_ADDRESS,
        function_name="open_case",
        args=[AGENT, "Test complaint", "https://en.wikipedia.org/wiki/Python_(programming_language)"],
    )
    receipt = client.wait_for_transaction_receipt(hash=tx)
    assert receipt is not None


def test_case_not_found():
    client = create_client(chain=localnet)
    result = client.read_contract(address=CONTRACT_ADDRESS, function_name="get_case", args=[999999])
    assert result == "NOT_FOUND"
