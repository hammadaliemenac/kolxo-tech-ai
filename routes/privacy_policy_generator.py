from fastapi import APIRouter
from ollama import generate
from pydantic import BaseModel
router = APIRouter()

# Privacy Policy Generator Endpoint
class PrivacyPolicyRequest(BaseModel):
    policy_name: str = "Privacy Policy"
    content_language: str = "english"
    company_name: str = "Alharam"
    company_email: str = "hammadali.emenac@gmail.com"
    company_contact: str = "09874561233"
    company_domain: str = "alharamtravel.co.uk"
    data_protection_officer_contract: str = "on"
    company_services: str = "Tourism COmpany offers: international Tours"
    data_protection_measures: str = "yes"
    data_third_party: str = "yes"
    cookie_policy_url: str = "alharamtravel.co.uk/cookie-policy"
    data_transfer: str = "yes"
    age_restriction: str = "yes"
    data_communication: str = "yes"
    data_marketing: str = "yes"
    data_breach: str = "yes"
    data_policy: str = "yes"
    data_updates: str = "yes"

@router.post("/privacy-policy-generator/")
def read_item(request: PrivacyPolicyRequest):
    # Prepare the prompt for the OpenAI API
    prompt = f"Generate a privacy policy based on the following data:\n"
    prompt += f"Policy Name: {request.policy_name}\n"
    prompt += f"Content Language: {request.content_language}\n"
    prompt += f"Company Name: {request.company_name}\n"
    prompt += f"Company Email: {request.company_email}\n"
    prompt += f"Company Contact: {request.company_contact}\n"
    prompt += f"Company Domain: {request.company_domain}\n"
    prompt += f"Do you have a Data Protection Officer (DPO): {request.data_protection_officer_contract}\n"
    prompt += f"Services and products does company provide:  {request.company_services}\n"
    prompt += f"Are you using any data protection Measures: {request.data_protection_measures}\n"
    prompt += f"Do you share personal data with third-party service providers: {request.data_third_party}\n"
    prompt += f"Cookie Policy URL: {request.cookie_policy_url}\n"
    prompt += f"Do you transfer data to countries outside the EEA: {request.data_transfer}\n"
    prompt += f"Does your website have age requirements: {request.age_restriction}\n"
    prompt += f"Do you transfer data to countries outside the EEA for communication: {request.data_communication}\n"
    prompt += f"Do you transfer data to countries outside the EEA for marketing: {request.data_marketing}\n"
    prompt += f"Do you want to add a response time for data breach notifications: {request.data_breach}\n"
    prompt += f"Do you require opt-in for material changes: {request.data_policy}\n"
    prompt += f"Do you want to notify users of policy updates: {request.data_updates}\n"
    prompt += f"Please write the privacy policy in clear and formal {request.content_language} language, ensuring that it includes necessary data protection clauses and complies with relevant laws like GDPR and CCPA. The response should be in HTML."

    response = generate(
        model='llama3',
        prompt=prompt
    )
    return {"query": request.policy_name, "content": response.response}
