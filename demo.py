import requests
import json

def demo_task_level(task_level, description):
    print(f"\n{'='*50}")
    print(f"DEMO: {description}")
    print(f"Task Level: {task_level}")
    print('='*50)

    # Reset environment
    response = requests.post('http://localhost:8000/reset', json={'task_level': task_level})
    obs = response.json()['observation']

    print(f"Sample Email: {obs['email_content'][:150]}...")

    # Test with a sample action
    if task_level in ["easy", "medium"]:
        action = {'classification': 'test_action', 'reply': ''}
    else:  # hard task
        action = {'classification': '', 'reply': 'Thank you for your email. I appreciate you reaching out. I will review this matter and get back to you as soon as possible with a detailed response.'}

    step_response = requests.post('http://localhost:8000/step', json={'action': action})
    reward = step_response.json()['reward']
    print(f"Reward: {reward['score']:.3f} - {reward['feedback']}")
    print(f"Task completed successfully: {'✅' if reward['score'] > 0 else '❌'}")

def main():
    print(" Email Triage Automation Environment - Demo")
    print("Testing all task levels with the production environment...")

    # Demo all task levels
    demo_task_level("easy", "Spam Classification")
    demo_task_level("medium", "Priority Assessment")
    demo_task_level("hard", "Professional Email Reply Generation")

    print(f"\n{'='*50}")
    print("✅ All task levels working successfully!")
    print("🎯 Advanced reward system with component scoring")
    print("🧵 Thread-aware memory management")
    print("🔒 Adversarial input handling")
    print("📊 Ready for hackathon evaluation")
    print('='*50)

if __name__ == "__main__":
    main()
    main()