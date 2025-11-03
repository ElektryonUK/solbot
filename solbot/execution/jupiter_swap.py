from __future__ import annotations
import os
import base64
import json
import httpx
from typing import Any
from solbot.core.logger import logger
from solana.keypair import Keypair
from solana.transaction import Transaction

class JupiterSwap:
    def __init__(self):
        # Use same base as quoter for consistency
        self.base = os.getenv("JUP_BASE", "https://lite-api.jup.ag/ultra/v1")
        logger.info("JupiterSwap initialized", extra={"base_url": self.base})

    async def build_swap(
        self,
        input_mint: str,
        output_mint: str,
        amount: int,
        slippage_bps: int,
        user_pubkey: str,
        prioritization_micro_lamports: int | None = None,
    ) -> dict[str, Any]:
        logger.info("Starting swap build", extra={
            "input_mint": input_mint,
            "output_mint": output_mint,
            "amount": amount,
            "slippage_bps": slippage_bps,
            "user_pubkey": user_pubkey[:8] + "...",  # Log first 8 chars for debugging
            "priority_fee": prioritization_micro_lamports
        })
        
        try:
            # Step 1: Get order from Jupiter Ultra
            order_url = f"{self.base}/order"
            params = {
                "inputMint": input_mint,
                "outputMint": output_mint,
                "amount": str(amount),
                "slippageBps": slippage_bps,
                "taker": user_pubkey,
            }
            if prioritization_micro_lamports:
                params["priorityFee"] = prioritization_micro_lamports
                
            logger.info("Requesting order", extra={"url": order_url, "params": params})
            
            async with httpx.AsyncClient(timeout=15) as client:
                logger.info("Making GET request to order endpoint")
                r = await client.get(order_url, params=params)
                logger.info("Order request response", extra={
                    "status_code": r.status_code,
                    "headers": dict(r.headers),
                    "response_size": len(r.content)
                })
                
                r.raise_for_status()
                order_data = r.json()
                logger.info("Order data received", extra={
                    "has_transaction": "transaction" in order_data,
                    "has_request_id": "requestId" in order_data,
                    "keys": list(order_data.keys())
                })
                
                # Step 2: Sign the transaction locally
                if "transaction" not in order_data or "requestId" not in order_data:
                    raise ValueError(f"Invalid order response: {order_data}")
                
                tx_b64 = order_data["transaction"]
                request_id = order_data["requestId"]
                
                logger.info("Signing transaction locally", extra={
                    "tx_length": len(tx_b64),
                    "request_id": request_id
                })
                
                # Decode and sign transaction
                tx_bytes = base64.b64decode(tx_b64)
                transaction = Transaction.deserialize(tx_bytes)
                
                # Get keypair from env
                keypair_str = os.getenv("USER_KEYPAIR")
                if not keypair_str:
                    raise ValueError("USER_KEYPAIR not found in environment")
                    
                logger.info("Loading keypair", extra={"keypair_format": "base58" if len(keypair_str) < 100 else "json"})
                
                if keypair_str.startswith('['):
                    # JSON array format
                    keypair_data = json.loads(keypair_str)
                    keypair = Keypair.from_bytes(bytes(keypair_data))
                else:
                    # Base58 format
                    keypair = Keypair.from_base58_string(keypair_str)
                
                logger.info("Keypair loaded", extra={"pubkey_matches": str(keypair.pubkey()) == user_pubkey})
                
                # Sign the transaction
                transaction.sign(keypair)
                signed_tx_b64 = base64.b64encode(transaction.serialize()).decode()
                
                logger.info("Transaction signed", extra={"signed_tx_length": len(signed_tx_b64)})
                
                # Step 3: Execute the signed transaction
                execute_url = f"{self.base}/execute"
                execute_payload = {
                    "signedTransaction": signed_tx_b64,
                    "requestId": request_id
                }
                
                logger.info("Executing signed transaction", extra={
                    "url": execute_url,
                    "payload_keys": list(execute_payload.keys())
                })
                
                execute_response = await client.post(execute_url, json=execute_payload)
                logger.info("Execute response", extra={
                    "status_code": execute_response.status_code,
                    "response_size": len(execute_response.content)
                })
                
                execute_response.raise_for_status()
                result = execute_response.json()
                
                logger.info("Transaction executed successfully", extra={
                    "result_keys": list(result.keys())
                })
                
                return result
                
        except Exception as e:
            logger.error("Swap build failed", extra={
                "error_type": type(e).__name__,
                "error_message": str(e),
                "input_mint": input_mint,
                "output_mint": output_mint,
                "amount": amount
            })
            raise
