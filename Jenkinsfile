pipeline {
  agent any
  
  // ✅ GitHub Webhook Trigger Configuration
  triggers {
    githubPush()
    pollSCM('H/15 * * * *')
  }
  
  options {
    buildDiscarder(logRotator(numToKeepStr: '10'))
    timeout(time: 30, unit: 'MINUTES')
    disableConcurrentBuilds()
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
        checkout scm
        script {
          echo "✅ Code checked out successfully"
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
          cp k8s/deployment.yaml k8s/deployment.yaml.bak
          sed -i "s|IMAGE_TAG|${IMAGE_TAG}|g" k8s/deployment.yaml
          kubectl apply -f k8s/ --validate=false
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
          echo "Check again in 2-3 minutes: kubectl get svc flask-service"
          echo ""
        '''
      }
    }
  }
  
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
        echo "Pipeline execution completed"
        echo "Build URL: ${BUILD_URL}"
        echo "======================================"
      }
    }
  }
}
