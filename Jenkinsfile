pipeline {
  agent any
  
  // ✅ GitHub Webhook Trigger Configuration
  triggers {
    // Primary: GitHub webhook trigger (real-time)
    githubPush()
    
    // Backup: Poll SCM every 15 minutes (in case webhook fails)
    pollSCM('H/15 * * * *')
  }
  
  // ✅ Pipeline Options
  options {
    // Keep only last 10 builds to save space
    buildDiscarder(logRotator(numToKeepStr: '10'))
    
    // Timeout if pipeline takes more than 30 minutes
    timeout(time: 30, unit: 'MINUTES')
    
    // Disable concurrent builds
    disableConcurrentBuilds()
    
    // Add timestamps to console output
    timestamps()
  }
  
  environment {
    AWS_REGION        = "us-east-1"
    CLUSTER_NAME      = "flask-eks"
    AWS_ACCOUNT_ID    = "816069153839"
    ECR_REPO          = "myrepo_flask"
    IMAGE_TAG         = "${BUILD_NUMBER}"
    ECR_URI           = "${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com/${ECR_REPO}"
    KUBECONFIG        = "/var/lib/jenkins/.kube/config"
    PATH              = "/usr/local/bin:/usr/bin:/bin"
    AWS_DEFAULT_REGION= "us-east-1"
  }
  
  stages {
    stage('Checkout') {
      steps {
        script {
          echo "🔄 Checking out code from GitHub..."
        }
        // Using 'checkout scm' is better than hardcoding git URL
        // It automatically uses the repo configured in Jenkins job
        checkout scm
        
        // Alternative: If you want to keep explicit git command
        // git branch: 'main', url: 'https://github.com/yuvanreddy/flask-eks-cicd.git'
        
        script {
          echo "✅ Code checked out successfully"
          // Show last commit info
          sh 'git log -1 --oneline'
        }
      }
    }
    
    stage('Build Image') {
      steps {
        script {
          echo "🐳 Building Docker image: ${ECR_REPO}:${IMAGE_TAG}"
        }
        sh '''
          docker build -t ${ECR_REPO}:${IMAGE_TAG} app/
        '''
        script {
          echo "✅ Docker image built successfully"
        }
      }
    }
    
    stage('Login to ECR') {
      steps {
        script {
          echo "🔐 Logging into AWS ECR..."
        }
        sh '''
          aws ecr get-login-password --region ${AWS_REGION} | \
            docker login --username AWS --password-stdin \
            ${AWS_ACCOUNT_ID}.dkr.ecr.${AWS_REGION}.amazonaws.com
        '''
        script {
          echo "✅ Successfully logged into ECR"
        }
      }
    }
    
    stage('Push Image') {
      steps {
        script {
          echo "📤 Pushing image to ECR: ${ECR_URI}:${IMAGE_TAG}"
        }
        sh '''
          docker tag ${ECR_REPO}:${IMAGE_TAG} ${ECR_URI}:${IMAGE_TAG}
          docker push ${ECR_URI}:${IMAGE_TAG}
          
          # Also tag as 'latest' for convenience
          docker tag ${ECR_REPO}:${IMAGE_TAG} ${ECR_URI}:latest
          docker push ${ECR_URI}:latest
        '''
        script {
          echo "✅ Image pushed to ECR successfully"
        }
      }
    }
    
    stage('Update kubeconfig') {
      steps {
        script {
          echo "⚙️ Updating kubeconfig for EKS cluster: ${CLUSTER_NAME}"
        }
        sh '''
          aws eks update-kubeconfig --region ${AWS_REGION} --name ${CLUSTER_NAME}
          kubectl config current-context
        '''
        script {
          echo "✅ Kubeconfig updated successfully"
        }
      }
    }
    
    stage('Apply aws-auth RBAC') {
      steps {
        script {
          echo "🔑 Applying aws-auth RBAC configuration..."
        }
        sh '''
          kubectl apply -f k8s/aws-auth.yaml --validate=false
        '''
        script {
          echo "✅ RBAC configuration applied"
        }
      }
    }
    
    stage('Deploy to EKS') {
      steps {
        script {
          echo "🚀 Deploying to EKS with image tag: ${IMAGE_TAG}"
        }
        sh '''
          # Create backup of deployment file
          cp k8s/deployment.yaml k8s/deployment.yaml.bak
          
          # Replace IMAGE_TAG placeholder with actual build number
          sed -i "s|IMAGE_TAG|${IMAGE_TAG}|g" k8s/deployment.yaml
          
          # Apply all Kubernetes manifests
          kubectl apply -f k8s/ --validate=false
          
          # Restore original deployment file
          mv k8s/deployment.yaml.bak k8s/deployment.yaml
        '''
        script {
          echo "✅ Deployment applied to EKS"
        }
      }
    }
    
    stage('Wait for Rollout') {
      steps {
        script {
          echo "⏳ Waiting for deployment to complete..."
        }
        sh '''
          # Wait for deployment to finish rolling out
          kubectl rollout status deployment/flask-deployment --timeout=5m
        '''
        script {
          echo "✅ Deployment rolled out successfully"
        }
      }
    }
    
    stage('Verify + Print URL') {
      steps {
        script {
          echo "🔍 Verifying deployment and fetching service URL..."
        }
        sh '''
          echo ""
          echo "======================================"
          echo "        DEPLOYMENT STATUS"
          echo "======================================"
          
          echo ""
          echo "=== PODS ==="
          kubectl get pods -o wide
          
          echo ""
          echo "=== DEPLOYMENTS ==="
          kubectl get deployments
          
          echo ""
          echo "=== SERVICES ==="
          kubectl get svc flask-service
          
          echo ""
          echo "======================================"
          echo "    FETCHING LOADBALANCER URL"
          echo "======================================"
          
          # Wait for LoadBalancer URL (max 5 minutes)
          for i in {1..30}; do
            URL=$(kubectl get svc flask-service -o jsonpath='{.status.loadBalancer.ingress[0].hostname}' 2>/dev/null || true)
            if [ ! -z "$URL" ]; then
              echo ""
              echo "✅✅✅ SUCCESS! ✅✅✅"
              echo ""
              echo "🌐 Flask App URL: http://$URL"
              echo ""
              echo "Test your app:"
              echo "  curl http://$URL"
              echo ""
              exit 0
            fi
            echo "Attempt $i/30: Waiting for LoadBalancer URL... (${i}0 seconds)"
            sleep 10
          done
          
          echo ""
          echo "⚠️ LoadBalancer URL not assigned yet."
          echo "This is normal for new services. Check again in 2-3 minutes:"
          echo ""
          echo "  kubectl get svc flask-service"
          echo ""
        '''
      }
    }
  }
  
  // ✅ Post-build Actions
  post {
    success {
      script {
        echo ""
        echo "🎉🎉🎉 PIPELINE COMPLETED SUCCESSFULLY! 🎉🎉🎉"
        echo ""
        echo "Build Number: ${BUILD_NUMBER}"
        echo "Image: ${ECR_URI}:${IMAGE_TAG}"
        echo ""
      }
      
      // Optional: Clean up old Docker images to save space
      sh '''
        echo "🧹 Cleaning up old Docker images..."
        docker image prune -af --filter "until=24h" || true
      '''
    }
    
    failure {
      script {
        echo ""
        echo "❌❌❌ PIPELINE FAILED! ❌❌❌"
        echo ""
        echo "Build Number: ${BUILD_NUMBER}"
        echo "Check logs above for error details"
        echo ""
      }
    }
    
    always {
      script {
        echo ""
        echo "======================================"
        echo "Pipeline execution completed at: ${new Date()}"
        echo "Build URL: ${BUILD_URL}"
        echo "======================================"
      }
      
      // Optional: Send notifications (uncomment if you set up email/Slack)
      // emailext (
      //   subject: "Jenkins Build ${currentBuild.result}: ${env.JOB_NAME} #${env.BUILD_NUMBER}",
      //   body: "Check console output at: ${env.BUILD_URL}",
      //   to: "your-email@example.com"
      // )
    }
    
    cleanup {
      // Clean up workspace after build (optional)
      // cleanWs()
    }
  }
}
