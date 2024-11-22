import os
import streamlit as st
from foundry import UserTokenAuth, ConfidentialClientAuth
from foundry.v2 import FoundryClient
from dotenv import load_dotenv


load_dotenv()


@st.cache_resource
def get_foundry_client() -> FoundryClient:
    """Returns a client with (test) user token authentication."""
    hostname = os.environ["HOSTNAME"]
    return FoundryClient(
        auth=UserTokenAuth(
            hostname=hostname,
            token=os.environ["BEARER_TOKEN"],
        ),
        hostname=hostname,
    )


@st.cache_resource
def get_foundry_oauth_client() -> FoundryClient:
    """Returns a client with OAuth Client (client credentials) authentication."""
    hostname = os.environ["HOSTNAME"]
    auth = ConfidentialClientAuth(
        client_id=os.environ["CLIENT_ID"],
        client_secret=os.environ["CLIENT_SECRET"],
        hostname=hostname,
        scopes=["api:aip-agents-read", "api:aip-agents-write"],
    )
    auth.sign_in_as_service_user()
    return FoundryClient(auth=auth, hostname=hostname)


with st.sidebar:
    aip_agent_rid = st.text_input("AIP Agent RID", key="aip_agent_rid")
    "[Create an AIP Agent](https://www.palantir.com/docs/foundry/agent-studio/overview/)"
    "[Create an OAuth Client](https://www.palantir.com/docs/foundry/ontology-sdk/create-a-new-osdk/#create-a-new-developer-console-application)"

st.title("💬 Chatbot")
st.caption("🚀 A Streamlit chatbot powered by AIP Agents")
if "messages" not in st.session_state:
    st.session_state["messages"] = [{"role": "assistant", "content": "How can I help you?"}]

for msg in st.session_state.messages:
    st.chat_message(msg["role"]).write(msg["content"])

if prompt := st.chat_input():
    if not aip_agent_rid:
        st.info("Please add your AIP Agent RID to continue.")
        st.stop()

    client = get_foundry_client()
    st.session_state.messages.append({"role": "user", "content": prompt})
    st.chat_message("user").write(prompt)

    if "session_rid" not in st.session_state:
        st.session_state["session_rid"] = client.aip_agents.Agent.Session.create(aip_agent_rid, preview=True).rid

    session_rid = st.session_state["session_rid"]

    response = client.aip_agents.Agent.Session.blocking_continue(
        agent_rid=aip_agent_rid,
        session_rid=session_rid,
        parameter_inputs={},
        user_input={"text": prompt},
        preview=True
    )

    msg = response.agent_markdown_response
    st.session_state.messages.append({"role": "assistant", "content": msg})
    st.chat_message("assistant").write(msg)
