import sys
import os
import asyncio
import json
import random
import string

# Add backend to path so we can import core modules
# If running in container /app, adding current directory is enough to import 'core'
sys.path.append(os.path.dirname(__file__))
# If running locally outside backend, add parent
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

try:
    # Try importing assuming we are OUTSIDE the backend folder (local dev)
    from backend.core.workflow_runtime import WorkflowEngine, WorkflowDefinition, WorkflowNode, WorkflowContext
except ImportError:
    # Try importing assuming we are INSIDE the backend folder (docker container /app)
    # The container structure is /app/core, not /app/backend/core
    from core.workflow_runtime import WorkflowEngine, WorkflowDefinition, WorkflowNode, WorkflowContext

# --- 1. Define Business Handlers (The Logic) ---

async def handle_tool_random_string(config: dict, context: WorkflowContext):
    """
    Real implementation of generating a random verification code.
    """
    length = int(config.get('length', 6))
    chars = string.digits # Numeric code for OTP
    code = ''.join(random.choice(chars) for _ in range(length))
    
    print(f"   [HANDLER] Generated Random Code: {code}")
    return {"value": code}

async def handle_action_send_email(config: dict, context: WorkflowContext):
    """
    Real implementation of sending email (Mocking SMTP for this script).
    Here is where we verify that variables were correctly passed!
    """
    # 1. Extract params (These are already RESOLVED by the engine!)
    to_email = config.get('to')
    template_code = config.get('template_code')
    variables = config.get('variables', {})
    
    # 2. Validation
    if not to_email:
        raise ValueError("Missing 'to' address")
        
    # 3. Simulate MailService.send_template_email
    # In production, this would be: await mail_service.send(...)
    print(f"   [HANDLER] Calling MailService...")
    print(f"             To: {to_email}")
    print(f"             Template: {template_code}")
    print(f"             Data Transformed: {json.dumps(variables)}")
    
    # Check if 'code' variable exists (PROOF OF CONCEPT)
    recieved_code = variables.get('code')
    if recieved_code:
        print(f"             ✅ SUCCESS: Verification Code '{recieved_code}' received!")
    else:
        print(f"             ❌ ERROR: Verification Code is MISSING!")
        
    return {"status": "sent", "provider": "mock_smtp"}

# --- 2. Define the Workflow (The Configuration) ---

def create_password_reset_workflow():
    """
    Creates the JSON structure that mimics what Vue Flow would produce.
    Flow: Start -> Generate Code -> Send Email
    """
    
    # Node 1: Start
    node_start = WorkflowNode(
        id="node_1",
        type="start",
        label="Start",
        next_node_id="node_2"
    )
    
    # Node 2: Generate Random Code
    node_generate = WorkflowNode(
        id="node_2",
        type="tool_random_string",
        label="Generate OTP",
        config={
            "length": 6,
            "type": "numeric"
        },
        next_node_id="node_3"
    )
    
    # Node 3: Send Email
    # CRITICAL: This is where we configure the MAPPING
    node_email = WorkflowNode(
        id="node_3",
        type="action_send_email",
        label="Send Reset Email",
        config={
            "to": "{{trigger.user.email}}",  # Map from Trigger
            "template_code": "auth_verify_code",
            "variables": {
                # MAP 'code' parameter to the RESULT of Node 2
                "code": "{{steps.node_2.value}}", 
                "name": "{{trigger.user.name}}"
            }
        },
        next_node_id=None # End
    )
    
    return WorkflowDefinition(
        id="wf_password_reset",
        name="Password Reset Flow",
        start_node_id="node_1",
        nodes={
            "node_1": node_start,
            "node_2": node_generate,
            "node_3": node_email
        }
    )

# --- 3. Run Simulation ---

async def main():
    print("=== WORKFLOW ENGINE SIMULATION: PASSWORD RESET ===")
    
    # A. Register Handlers
    handlers = {
        "tool_random_string": handle_tool_random_string,
        "action_send_email": handle_action_send_email
    }
    
    # B. Load Definition
    workflow_def = create_password_reset_workflow()
    
    # C. Prepare Trigger Data (Simulate user clicking 'Forgot Password')
    trigger_payload = {
        "event": "password.forgot",
        "user": {
            "id": 101,
            "email": "test_user@talentmail.com",
            "name": "Test User"
        }
    }
    
    # D. Execute
    engine = WorkflowEngine(workflow_def, handlers=handlers)
    final_context = await engine.run(trigger_payload)
    
    print("\n=== SIMULATION COMPLETE ===")
    print("Final Context Dump (Proof of Persistence):")
    print(json.dumps(final_context.data, default=str, indent=2))

if __name__ == "__main__":
    asyncio.run(main())