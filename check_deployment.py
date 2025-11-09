#!/usr/bin/env python3
"""
Script to check deployment status
"""
import requests
import time

def check_railway_deployment():
    """Check if Railway backend is deployed and working"""
    railway_url = "https://pe-intelligence-production.up.railway.app"
    
    print("🚀 Checking Railway backend deployment...")
    
    try:
        # Check health endpoint
        response = requests.get(f"{railway_url}/", timeout=10)
        if response.status_code == 200:
            print("✅ Railway backend is deployed and responding!")
            print(f"   Status: {response.status_code}")
            print(f"   URL: {railway_url}")
            return True
        else:
            print(f"⚠️  Railway backend responded with status: {response.status_code}")
            return False
    except requests.exceptions.RequestException as e:
        print(f"❌ Railway backend not accessible: {e}")
        print("   This is normal if deployment is still in progress...")
        return False

def check_vercel_deployment():
    """Check if Vercel frontend is deployed"""
    # This will be updated once we know the Vercel URL
    print("📱 Vercel frontend deployment will be checked after setup...")
    return True

if __name__ == "__main__":
    print("🔍 Checking deployment status...\n")
    
    railway_ok = check_railway_deployment()
    vercel_ok = check_vercel_deployment()
    
    print("\n📊 Deployment Summary:")
    print(f"   Backend (Railway): {'✅ Ready' if railway_ok else '⏳ Deploying...'}")
    print(f"   Frontend (Vercel): ⏳ Pending setup")
    
    if railway_ok:
        print("\n🎉 Backend is ready! You can now:")
        print("   1. Set up environment variables in Railway dashboard")
        print("   2. Deploy frontend to Vercel")
        print("   3. Test the complete application")
    else:
        print("\n⏳ Backend is still deploying. Please wait a few minutes and try again.")