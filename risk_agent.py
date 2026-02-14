"""
Risk Agent - Risk Assessment and Prediction

This agent identifies, assesses, and prioritizes project risks using ML models.
"""

import logging
from typing import Any, Dict, List
import json

from langchain.tools import Tool

from .base_agent import BaseAgent

logger = logging.getLogger(__name__)


class RiskAgent(BaseAgent):
    """
    Risk Agent for project risk assessment and prediction.
    
    Uses ML models to predict risk probability and impact.
    """
    
    def __init__(self, **kwargs):
        super().__init__(
            name="Risk",
            description="Identifies and assesses project risks using ML-powered predictions",
            **kwargs
        )
        
        # Risk categories
        self.risk_categories = [
            "technical",
            "resource",
            "schedule",
            "security",
            "organizational"
        ]
        
    def get_system_prompt(self) -> str:
        """System prompt for risk agent."""
        return """You are the Risk Agent for AutoPMO, an expert in project risk management.

Your expertise includes:
- PMBOK risk management processes
- Risk identification techniques (SWOT, brainstorming, Delphi)
- Qualitative and quantitative risk analysis
- Risk response strategies (avoid, mitigate, transfer, accept)
- Risk monitoring and control

Risk Categories:
1. Technical: Technology complexity, integration issues
2. Resource: Availability, skills gaps, turnover
3. Schedule: Deadline pressure, dependencies
4. Security: Vulnerabilities, compliance gaps
5. Organizational: Stakeholder alignment, process issues

For each risk, provide:
- Risk ID and description
- Category
- Probability (Low/Medium/High or 0-100%)
- Impact (1-5 scale)
- Risk Score (Probability × Impact)
- Mitigation strategies
- Owner assignment

Use data-driven analysis when available.
Be realistic but not alarmist.
Focus on actionable mitigations.
"""
    
    def register_tools(self) -> List[Tool]:
        """Register risk assessment tools."""
        tools = [
            Tool(
                name="predict_risk",
                func=self._predict_risk,
                description="Use ML model to predict risk probability. Input: project characteristics in JSON"
            ),
            Tool(
                name="calculate_risk_score",
                func=self._calculate_risk_score,
                description="Calculate risk score from probability and impact. Input: 'probability,impact'"
            ),
            Tool(
                name="generate_risk_register",
                func=self._generate_risk_register,
                description="Generate risk register for project. Input: project description"
            ),
            Tool(
                name="suggest_mitigation",
                func=self._suggest_mitigation,
                description="Suggest mitigation strategies for a risk. Input: risk description"
            ),
        ]
        return tools
    
    def _predict_risk(self, project_json: str) -> str:
        """
        Predict risk using ML model.
        
        Args:
            project_json: Project characteristics in JSON
            
        Returns:
            Risk prediction results
        """
        try:
            # In production, this would call the KServe model endpoint
            # For now, return mock prediction
            
            project_data = json.loads(project_json) if isinstance(project_json, str) else project_json
            
            # Mock ML model logic
            complexity_score = {
                "low": 0.2,
                "medium": 0.5,
                "high": 0.8
            }.get(project_data.get("complexity", "medium"), 0.5)
            
            team_experience = project_data.get("team_experience_years", 3)
            experience_factor = max(0.2, 1.0 - (team_experience / 10))
            
            risk_probability = min(0.95, (complexity_score + experience_factor) / 2)
            
            return json.dumps({
                "risk_probability": round(risk_probability, 2),
                "risk_category": "technical" if complexity_score > 0.6 else "resource",
                "confidence": 0.82,
                "factors": {
                    "complexity": complexity_score,
                    "team_experience": experience_factor
                },
                "recommendation": "High risk - recommend experienced tech lead"
            }, indent=2)
            
        except Exception as e:
            logger.error(f"Risk prediction failed: {e}")
            return json.dumps({"error": str(e)})
    
    def _calculate_risk_score(self, risk_params: str) -> str:
        """
        Calculate risk score.
        
        Args:
            risk_params: "probability,impact" string
            
        Returns:
            Risk score and priority
        """
        try:
            probability, impact = map(float, risk_params.split(","))
            score = probability * impact
            
            if score > 3.5:
                priority = "Critical"
            elif score > 2.5:
                priority = "High"
            elif score > 1.5:
                priority = "Medium"
            else:
                priority = "Low"
            
            return f"Risk Score: {score:.2f} | Priority: {priority}"
            
        except Exception as e:
            return f"Error calculating score: {e}"
    
    def _generate_risk_register(self, project_description: str) -> str:
        """
        Generate risk register.
        
        Args:
            project_description: Project description
            
        Returns:
            Risk register in YAML format
        """
        # In production, this would use ML to identify risks
        # For now, return template based on common risks
        
        risks = [
            {
                "id": "RISK-001",
                "description": "Insufficient team experience with target platform",
                "category": "resource",
                "probability": 0.6,
                "impact": 4,
                "score": 2.4,
                "mitigation": "Hire experienced consultant, provide training",
                "owner": "tech_lead"
            },
            {
                "id": "RISK-002",
                "description": "Integration complexity with legacy systems",
                "category": "technical",
                "probability": 0.7,
                "impact": 4,
                "score": 2.8,
                "mitigation": "Proof of concept for critical integrations",
                "owner": "architect"
            },
            {
                "id": "RISK-003",
                "description": "Aggressive timeline with limited buffer",
                "category": "schedule",
                "probability": 0.5,
                "impact": 3,
                "score": 1.5,
                "mitigation": "Add 20% buffer, prioritize MVP features",
                "owner": "project_manager"
            },
            {
                "id": "RISK-004",
                "description": "Security compliance requirements unclear",
                "category": "security",
                "probability": 0.4,
                "impact": 5,
                "score": 2.0,
                "mitigation": "Early engagement with security team",
                "owner": "security_lead"
            }
        ]
        
        return json.dumps({"risks": risks}, indent=2)
    
    def _suggest_mitigation(self, risk_description: str) -> str:
        """
        Suggest mitigation strategies.
        
        Args:
            risk_description: Description of the risk
            
        Returns:
            Mitigation recommendations
        """
        # Simple keyword-based suggestions
        # In production, this would use LLM or ML model
        
        mitigations = []
        
        if "experience" in risk_description.lower():
            mitigations.append("• Hire experienced consultants or contractors")
            mitigations.append("• Provide comprehensive training program")
            mitigations.append("• Pair junior team members with seniors")
        
        if "security" in risk_description.lower():
            mitigations.append("• Conduct early security review")
            mitigations.append("• Implement security testing in CI/CD")
            mitigations.append("• Engage security team from day one")
        
        if "timeline" in risk_description.lower() or "schedule" in risk_description.lower():
            mitigations.append("• Add buffer time (15-20%)")
            mitigations.append("• Identify MVP vs nice-to-have features")
            mitigations.append("• Use agile/iterative approach")
        
        if "integration" in risk_description.lower():
            mitigations.append("• Build proof-of-concept for critical paths")
            mitigations.append("• Create integration test environment early")
            mitigations.append("• Document all API contracts")
        
        if not mitigations:
            mitigations.append("• Regular risk review meetings")
            mitigations.append("• Maintain risk register")
            mitigations.append("• Assign risk owners")
        
        return "\n".join(mitigations)
    
    async def assess_project_risk(
        self,
        project_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Perform comprehensive project risk assessment.
        
        Args:
            project_data: Project characteristics and context
            
        Returns:
            Complete risk assessment with recommendations
        """
        logger.info("Performing project risk assessment")
        
        # Get ML prediction
        prediction = self._predict_risk(json.dumps(project_data))
        prediction_data = json.loads(prediction)
        
        # Generate risk register
        risk_register = self._generate_risk_register(
            project_data.get("description", "")
        )
        
        # Calculate overall risk score
        overall_risk = prediction_data.get("risk_probability", 0.5)
        
        if overall_risk > 0.7:
            risk_level = "High"
            recommendation = "Recommend risk mitigation plan before proceeding"
        elif overall_risk > 0.4:
            risk_level = "Medium"
            recommendation = "Monitor key risks closely"
        else:
            risk_level = "Low"
            recommendation = "Proceed with standard risk management"
        
        return {
            "overall_risk_level": risk_level,
            "risk_probability": overall_risk,
            "ml_prediction": prediction_data,
            "risk_register": json.loads(risk_register),
            "recommendation": recommendation,
            "next_steps": [
                "Review and approve risk register",
                "Assign risk owners",
                "Schedule risk review meetings",
                "Update risk register weekly"
            ]
        }
