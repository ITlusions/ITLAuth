# Keycloak PIM Implementatie met Standaard Helm Chart

**Praktische guide voor het toevoegen van PIM functionaliteit aan standaard Keycloak**

Deze guide laat zien hoe je Just-In-Time (PIM) access implementeert bovenop een standaard Keycloak installatie zonder de core image te wijzigen.

## Architectuur Overzicht

```
┌─────────────────────────────────────────────────────────┐
│           Standaard Keycloak Setup                      │
│  ┌───────────────────────────────────────────────────┐ │
│  │   Bitnami Keycloak Helm Chart                     │ │
│  │   + Standaard keycloak:23.0 image                 │ │
│  └───────────────────────────────────────────────────┘ │
└─────────────────────────────────────────────────────────┘
                          │
                          │ We voegen toe:
                          ▼
┌─────────────────────────────────────────────────────────┐
│           PIM Layer (Geen Keycloak Modificatie)         │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  PIM Controller (Separate Pod/Deployment)        │  │
│  │  - REST API voor elevation requests              │  │
│  │  - Keycloak Admin API client                     │  │
│  │  - PostgreSQL voor PIM assignments               │  │
│  │  - CronJob voor expiration cleanup               │  │
│  └──────────────────────────────────────────────────┘  │
│                                                          │
│  ┌──────────────────────────────────────────────────┐  │
│  │  ITLC CLI (Client Side)                          │  │
│  │  - Praat met PIM Controller API                  │  │
│  │  - Token mapper via Keycloak protocol mappers    │  │
│  └──────────────────────────────────────────────────┘  │
└─────────────────────────────────────────────────────────┘
```

**Belangrijkste inzicht:** We wijzigen Keycloak NIET, maar bouwen een controller die de Keycloak Admin API gebruikt om groepen dynamisch toe te wijzen.

## Implementatie Opties

### Optie 1: PIM Controller als Separate Service (Aanbevolen)

**Voordelen:**
- ✅ Geen custom Keycloak image nodig
- ✅ Eenvoudig te updaten (los van Keycloak)
- ✅ Werkt met elke Keycloak versie
- ✅ Kan geschaald worden (los van Keycloak)

**Nadelen:**
- Externe dependency (controller moet beschikbaar zijn)
- Iets meer latency (extra network hop)

### Optie 2: Event Listener Plugin (Geavanceerd)

**Voordelen:**
- Diep geïntegreerd in Keycloak
- Geen externe service nodig

**Nadelen:**
- ❌ Vereist custom Keycloak image
- ❌ Complexer om te onderhouden
- ❌ Keycloak restarts bij updates

## Stap-voor-Stap: PIM Controller Implementatie

### Stap 1: Deploy Standaard Keycloak (Blijft Ongewijzigd)

```bash
# Voeg Bitnami repo toe
helm repo add bitnami https://charts.bitnami.com/bitnami
helm repo update

# Deploy Keycloak zoals gebruikelijk
helm install keycloak bitnami/keycloak \
  --namespace auth \
  --create-namespace \
  --set auth.adminUser=admin \
  --set auth.adminPassword='changeme' \
  --set postgresql.enabled=true \
  --set postgresql.auth.password='postgres-password'
```

**Geen aanpassingen nodig aan Keycloak zelf!**

### Stap 2: Deploy PostgreSQL Database voor PIM

```yaml
# pim-postgresql.yaml
apiVersion: v1
kind: PersistentVolumeClaim
metadata:
  name: pim-postgres-pvc
  namespace: auth
spec:
  accessModes:
    - ReadWriteOnce
  resources:
    requests:
      storage: 10Gi
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pim-postgres
  namespace: auth
spec:
  replicas: 1
  selector:
    matchLabels:
      app: pim-postgres
  template:
    metadata:
      labels:
        app: pim-postgres
    spec:
      containers:
      - name: postgres
        image: postgres:15-alpine
        env:
        - name: POSTGRES_DB
          value: keycloak_pim
        - name: POSTGRES_USER
          value: pim
        - name: POSTGRES_PASSWORD
          valueFrom:
            secretKeyRef:
              name: pim-postgres-secret
              key: password
        ports:
        - containerPort: 5432
        volumeMounts:
        - name: data
          mountPath: /var/lib/postgresql/data
      volumes:
      - name: data
        persistentVolumeClaim:
          claimName: pim-postgres-pvc
---
apiVersion: v1
kind: Service
metadata:
  name: pim-postgres
  namespace: auth
spec:
  selector:
    app: pim-postgres
  ports:
  - port: 5432
    targetPort: 5432
---
apiVersion: v1
kind: Secret
metadata:
  name: pim-postgres-secret
  namespace: auth
type: Opaque
stringData:
  password: "secure-pim-password-change-me"
```

```bash
kubectl apply -f pim-postgresql.yaml
```

### Stap 3: Database Schema Initialisatie

```sql
-- pim-schema.sql
CREATE TABLE pim_assignments (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    user_id VARCHAR(255) NOT NULL,
    username VARCHAR(255) NOT NULL,
    role_name VARCHAR(255) NOT NULL,
    keycloak_group_id VARCHAR(255),
    
    granted_by VARCHAR(255),
    granted_at TIMESTAMP,
    expires_at TIMESTAMP NOT NULL,
    
    reason TEXT,
    ticket_reference VARCHAR(100),
    
    approval_required BOOLEAN DEFAULT FALSE,
    approved_by VARCHAR(255),
    approved_at TIMESTAMP,
    
    status VARCHAR(50) NOT NULL, -- pending, active, expired, revoked, denied
    
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW(),
    
    INDEX idx_user_active (user_id, status, expires_at),
    INDEX idx_expiration (expires_at, status),
    INDEX idx_status (status)
);

CREATE TABLE pim_audit_log (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    assignment_id UUID REFERENCES pim_assignments(id),
    action VARCHAR(50) NOT NULL, -- requested, approved, denied, activated, expired, revoked, extended
    actor VARCHAR(255) NOT NULL,
    timestamp TIMESTAMP DEFAULT NOW(),
    metadata JSONB,
    ip_address INET,
    user_agent TEXT
);

CREATE TABLE pim_eligible_roles (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    role_name VARCHAR(255) NOT NULL UNIQUE,
    display_name VARCHAR(255),
    description TEXT,
    keycloak_group_id VARCHAR(255) NOT NULL,
    
    approval_required BOOLEAN DEFAULT FALSE,
    max_duration_seconds INTEGER DEFAULT 28800, -- 8 hours
    default_duration_seconds INTEGER DEFAULT 7200, -- 2 hours
    
    mfa_required BOOLEAN DEFAULT TRUE,
    require_justification BOOLEAN DEFAULT FALSE,
    require_ticket BOOLEAN DEFAULT FALSE,
    
    eligible_groups TEXT[], -- Array of Keycloak group names
    approver_groups TEXT[], -- Array of approver group names
    min_approvers INTEGER DEFAULT 1,
    
    notify_on_activation TEXT[], -- Array of email addresses
    
    enabled BOOLEAN DEFAULT TRUE,
    created_at TIMESTAMP DEFAULT NOW(),
    updated_at TIMESTAMP DEFAULT NOW()
);

-- Example eligible roles
INSERT INTO pim_eligible_roles (
    role_name, display_name, description, keycloak_group_id,
    approval_required, max_duration_seconds, eligible_groups
) VALUES 
    ('k8s-production-read', 'Production Read Access', 'Read-only access to production Kubernetes', 
     'group-id-here', FALSE, 14400, ARRAY['k8s-developers', 'sre-team']),
    
    ('k8s-cluster-admin', 'Cluster Administrator', 'Full cluster administration access',
     'group-id-here', TRUE, 86400, ARRAY['sre-team']);
```

**Deploy schema:**
```bash
kubectl -n auth exec -i deployment/pim-postgres -- \
  psql -U pim -d keycloak_pim < pim-schema.sql
```

### Stap 4: PIM Controller Applicatie

**Tech stack:** Python (Flask) - eenvoudig en effectief

```python
# pim-controller/app.py
from flask import Flask, request, jsonify
from keycloak import KeycloakAdmin
from keycloak.exceptions import KeycloakError
import psycopg2
from datetime import datetime, timedelta
import os
import uuid

app = Flask(__name__)

# Configuratie
KEYCLOAK_URL = os.getenv('KEYCLOAK_URL', 'http://keycloak:8080')
KEYCLOAK_REALM = os.getenv('KEYCLOAK_REALM', 'production')
KEYCLOAK_ADMIN_USER = os.getenv('KEYCLOAK_ADMIN_USER', 'admin')
KEYCLOAK_ADMIN_PASSWORD = os.getenv('KEYCLOAK_ADMIN_PASSWORD')

DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://pim:password@pim-postgres:5432/keycloak_pim')

# Keycloak Admin client
keycloak_admin = KeycloakAdmin(
    server_url=KEYCLOAK_URL,
    username=KEYCLOAK_ADMIN_USER,
    password=KEYCLOAK_ADMIN_PASSWORD,
    realm_name=KEYCLOAK_REALM,
    verify=True
)

# Database connectie
def get_db():
    return psycopg2.connect(DATABASE_URL)

@app.route('/health', methods=['GET'])
def health():
    """Health check endpoint"""
    return jsonify({'status': 'healthy', 'timestamp': datetime.utcnow().isoformat()})

@app.route('/api/v1/elevate', methods=['POST'])
def request_elevation():
    """Request privilege elevation"""
    try:
        # Parse request
        data = request.json
        user_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        # Decode token en haal user info op
        user_info = keycloak_admin.introspect(user_token)
        if not user_info.get('active'):
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = user_info['sub']
        username = user_info.get('preferred_username')
        
        role_name = data.get('role_name')
        duration_seconds = data.get('duration', 7200)  # Default 2h
        reason = data.get('reason')
        ticket = data.get('ticket_reference')
        
        # Validate role exists and user is eligible
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT role_name, keycloak_group_id, approval_required, 
                   max_duration_seconds, eligible_groups, mfa_required,
                   require_justification, require_ticket
            FROM pim_eligible_roles 
            WHERE role_name = %s AND enabled = TRUE
        """, (role_name,))
        
        role = cur.fetchone()
        if not role:
            return jsonify({'error': f'Role {role_name} not found or not enabled'}), 404
        
        (role_name, group_id, approval_required, max_duration, 
         eligible_groups, mfa_required, require_justification, require_ticket) = role
        
        # Check duration limit
        if duration_seconds > max_duration:
            return jsonify({'error': f'Duration exceeds maximum of {max_duration} seconds'}), 400
        
        # Check if user is in eligible groups
        user_groups = keycloak_admin.get_user_groups(user_id)
        user_group_names = [g['name'] for g in user_groups]
        
        is_eligible = any(eg in user_group_names for eg in eligible_groups)
        if not is_eligible:
            return jsonify({'error': 'User not eligible for this role'}), 403
        
        # Check requirements
        if require_justification and not reason:
            return jsonify({'error': 'Justification required for this role'}), 400
        
        if require_ticket and not ticket:
            return jsonify({'error': 'Ticket reference required for this role'}), 400
        
        # Create PIM assignment
        assignment_id = str(uuid.uuid4())
        expires_at = datetime.utcnow() + timedelta(seconds=duration_seconds)
        
        status = 'pending' if approval_required else 'active'
        
        cur.execute("""
            INSERT INTO pim_assignments (
                id, user_id, username, role_name, keycloak_group_id,
                expires_at, reason, ticket_reference,
                approval_required, status, created_at
            ) VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
        """, (assignment_id, user_id, username, role_name, group_id,
              expires_at, reason, ticket, approval_required, status))
        
        # Audit log
        cur.execute("""
            INSERT INTO pim_audit_log (assignment_id, action, actor, metadata)
            VALUES (%s, %s, %s, %s)
        """, (assignment_id, 'requested', username, 
              {'reason': reason, 'ticket': ticket, 'duration': duration_seconds}))
        
        conn.commit()
        
        # If no approval required, activate immediately
        if not approval_required:
            activate_assignment(assignment_id, username, cur, conn)
        
        cur.close()
        conn.close()
        
        response = {
            'id': assignment_id,
            'role_name': role_name,
            'status': status,
            'expires_at': expires_at.isoformat(),
            'approval_required': approval_required
        }
        
        status_code = 202 if approval_required else 200
        return jsonify(response), status_code
        
    except Exception as e:
        app.logger.error(f"Elevation request failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

def activate_assignment(assignment_id, activated_by, cur, conn):
    """Activate a PIM assignment by adding user to Keycloak group"""
    
    # Get assignment details
    cur.execute("""
        SELECT user_id, role_name, keycloak_group_id, username
        FROM pim_assignments 
        WHERE id = %s
    """, (assignment_id,))
    
    user_id, role_name, group_id, username = cur.fetchone()
    
    # Add user to Keycloak group
    try:
        keycloak_admin.group_user_add(user_id, group_id)
        
        # Update assignment status
        cur.execute("""
            UPDATE pim_assignments 
            SET status = 'active', granted_at = NOW(), granted_by = %s
            WHERE id = %s
        """, (activated_by, assignment_id))
        
        # Audit log
        cur.execute("""
            INSERT INTO pim_audit_log (assignment_id, action, actor)
            VALUES (%s, %s, %s)
        """, (assignment_id, 'activated', activated_by))
        
        conn.commit()
        
        app.logger.info(f"Activated PIM assignment {assignment_id} for user {username}")
        
    except KeycloakError as e:
        app.logger.error(f"Failed to add user to Keycloak group: {str(e)}")
        raise

@app.route('/api/v1/assignments', methods=['GET'])
def list_assignments():
    """List active PIM assignments for current user"""
    try:
        user_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        user_info = keycloak_admin.introspect(user_token)
        
        if not user_info.get('active'):
            return jsonify({'error': 'Invalid token'}), 401
        
        user_id = user_info['sub']
        
        conn = get_db()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT id, role_name, granted_by, granted_at, expires_at, 
                   reason, ticket_reference, status
            FROM pim_assignments
            WHERE user_id = %s AND status = 'active'
            ORDER BY granted_at DESC
        """, (user_id,))
        
        assignments = []
        for row in cur.fetchall():
            assignments.append({
                'id': str(row[0]),
                'role_name': row[1],
                'granted_by': row[2],
                'granted_at': row[3].isoformat() if row[3] else None,
                'expires_at': row[4].isoformat(),
                'reason': row[5],
                'ticket_reference': row[6],
                'status': row[7]
            })
        
        cur.close()
        conn.close()
        
        return jsonify(assignments)
        
    except Exception as e:
        app.logger.error(f"Failed to list assignments: {str(e)}")
        return jsonify({'error': str(e)}), 500

@app.route('/api/v1/approve/<assignment_id>', methods=['POST'])
def approve_request(assignment_id):
    """Approve a pending elevation request"""
    try:
        data = request.json
        user_token = request.headers.get('Authorization', '').replace('Bearer ', '')
        
        user_info = keycloak_admin.introspect(user_token)
        if not user_info.get('active'):
            return jsonify({'error': 'Invalid token'}), 401
        
        approver_username = user_info.get('preferred_username')
        approved = data.get('approved', True)
        comment = data.get('comment')
        
        conn = get_db()
        cur = conn.cursor()
        
        # Get assignment
        cur.execute("""
            SELECT user_id, role_name, status FROM pim_assignments WHERE id = %s
        """, (assignment_id,))
        
        assignment = cur.fetchone()
        if not assignment:
            return jsonify({'error': 'Assignment not found'}), 404
        
        if assignment[2] != 'pending':
            return jsonify({'error': 'Assignment not pending approval'}), 400
        
        # TODO: Check if approver is authorized (verify group membership)
        
        if approved:
            # Activate assignment
            activate_assignment(assignment_id, approver_username, cur, conn)
            
            cur.execute("""
                UPDATE pim_assignments 
                SET approved_by = %s, approved_at = NOW()
                WHERE id = %s
            """, (approver_username, assignment_id))
            
            action = 'approved'
        else:
            # Deny assignment
            cur.execute("""
                UPDATE pim_assignments 
                SET status = 'denied', approved_by = %s, approved_at = NOW()
                WHERE id = %s
            """, (approver_username, assignment_id))
            
            action = 'denied'
        
        # Audit log
        cur.execute("""
            INSERT INTO pim_audit_log (assignment_id, action, actor, metadata)
            VALUES (%s, %s, %s, %s)
        """, (assignment_id, action, approver_username, {'comment': comment}))
        
        conn.commit()
        cur.close()
        conn.close()
        
        return jsonify({'status': action})
        
    except Exception as e:
        app.logger.error(f"Approval failed: {str(e)}")
        return jsonify({'error': str(e)}), 500

if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000)
```

**Requirements:**
```txt
# pim-controller/requirements.txt
Flask==3.0.0
python-keycloak==3.9.0
psycopg2-binary==2.9.9
gunicorn==21.2.0
```

**Dockerfile:**
```dockerfile
# pim-controller/Dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY app.py .

EXPOSE 5000

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5000", "app:app"]
```

### Stap 5: Deploy PIM Controller

```yaml
# pim-controller-deployment.yaml
apiVersion: v1
kind: ConfigMap
metadata:
  name: pim-controller-config
  namespace: auth
data:
  KEYCLOAK_URL: "http://keycloak:8080"
  KEYCLOAK_REALM: "production"
  KEYCLOAK_ADMIN_USER: "admin"
  DATABASE_URL: "postgresql://pim:secure-pim-password-change-me@pim-postgres:5432/keycloak_pim"
---
apiVersion: v1
kind: Secret
metadata:
  name: pim-controller-secret
  namespace: auth
type: Opaque
stringData:
  KEYCLOAK_ADMIN_PASSWORD: "changeme"  # Zelfde als Keycloak admin password
---
apiVersion: apps/v1
kind: Deployment
metadata:
  name: pim-controller
  namespace: auth
spec:
  replicas: 2
  selector:
    matchLabels:
      app: pim-controller
  template:
    metadata:
      labels:
        app: pim-controller
    spec:
      containers:
      - name: controller
        image: your-registry/pim-controller:latest  # Build en push eerst
        ports:
        - containerPort: 5000
        envFrom:
        - configMapRef:
            name: pim-controller-config
        env:
        - name: KEYCLOAK_ADMIN_PASSWORD
          valueFrom:
            secretKeyRef:
              name: pim-controller-secret
              key: KEYCLOAK_ADMIN_PASSWORD
        resources:
          requests:
            memory: "256Mi"
            cpu: "100m"
          limits:
            memory: "512Mi"
            cpu: "500m"
        livenessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 10
          periodSeconds: 30
        readinessProbe:
          httpGet:
            path: /health
            port: 5000
          initialDelaySeconds: 5
          periodSeconds: 10
---
apiVersion: v1
kind: Service
metadata:
  name: pim-controller
  namespace: auth
spec:
  selector:
    app: pim-controller
  ports:
  - port: 80
    targetPort: 5000
  type: ClusterIP
```

**Build en deploy:**
```bash
# Build image
cd pim-controller
docker build -t your-registry/pim-controller:latest .
docker push your-registry/pim-controller:latest

# Deploy
kubectl apply -f pim-controller-deployment.yaml
```

### Stap 6: Cleanup CronJob voor Expiration

```yaml
# pim-cleanup-cronjob.yaml
apiVersion: batch/v1
kind: CronJob
metadata:
  name: pim-cleanup
  namespace: auth
spec:
  schedule: "*/5 * * * *"  # Elke 5 minuten
  jobTemplate:
    spec:
      template:
        spec:
          containers:
          - name: cleanup
            image: your-registry/pim-controller:latest
            command:
            - python
            - -c
            - |
              import psycopg2
              from keycloak import KeycloakAdmin
              from datetime import datetime
              import os
              
              # Connect to database
              conn = psycopg2.connect(os.getenv('DATABASE_URL'))
              cur = conn.cursor()
              
              # Find expired assignments
              cur.execute("""
                  SELECT id, user_id, keycloak_group_id, username
                  FROM pim_assignments
                  WHERE status = 'active' AND expires_at < NOW()
              """)
              
              expired = cur.fetchall()
              
              if expired:
                  # Connect to Keycloak
                  keycloak_admin = KeycloakAdmin(
                      server_url=os.getenv('KEYCLOAK_URL'),
                      username=os.getenv('KEYCLOAK_ADMIN_USER'),
                      password=os.getenv('KEYCLOAK_ADMIN_PASSWORD'),
                      realm_name=os.getenv('KEYCLOAK_REALM')
                  )
                  
                  for assignment_id, user_id, group_id, username in expired:
                      try:
                          # Remove from Keycloak group
                          keycloak_admin.group_user_remove(user_id, group_id)
                          
                          # Update status
                          cur.execute("""
                              UPDATE pim_assignments 
                              SET status = 'expired' 
                              WHERE id = %s
                          """, (assignment_id,))
                          
                          # Audit log
                          cur.execute("""
                              INSERT INTO pim_audit_log (assignment_id, action, actor)
                              VALUES (%s, 'expired', 'system')
                          """, (assignment_id,))
                          
                          conn.commit()
                          
                          print(f"Expired assignment {assignment_id} for user {username}")
                          
                      except Exception as e:
                          print(f"Failed to expire assignment {assignment_id}: {str(e)}")
                          conn.rollback()
              
              cur.close()
              conn.close()
              
              print(f"Cleanup completed. Processed {len(expired)} expired assignments.")
            envFrom:
            - configMapRef:
                name: pim-controller-config
            env:
            - name: KEYCLOAK_ADMIN_PASSWORD
              valueFrom:
                secretKeyRef:
                  name: pim-controller-secret
                  key: KEYCLOAK_ADMIN_PASSWORD
          restartPolicy: OnFailure
```

```bash
kubectl apply -f pim-cleanup-cronjob.yaml
```

### Stap 7: ITLC CLI Configuratie

Update ITLC CLI om met PIM controller te praten:

```python
# itlc/config.py - Voeg toe
PIM_CONTROLLER_URL = os.getenv(
    'PIM_CONTROLLER_URL', 
    'http://pim-controller.auth.svc.cluster.local'
)
```

```python
# itlc/pim.py - Update endpoints
@pim.command()
@click.option('--role', required=True)
@click.option('--duration', default='8h')
@click.option('--reason')
@click.option('--ticket')
def elevate(role, duration, reason, ticket):
    """Request privilege elevation"""
    
    token = get_cached_token()
    
    # Parse duration naar seconden
    duration_seconds = parse_duration(duration)
    
    # Call PIM controller (niet direct Keycloak)
    response = requests.post(
        f"{PIM_CONTROLLER_URL}/api/v1/elevate",
        headers={"Authorization": f"Bearer {token}"},
        json={
            "role_name": role,
            "duration": duration_seconds,
            "reason": reason,
            "ticket_reference": ticket
        }
    )
    
    if response.status_code == 200:
        data = response.json()
        click.echo(f"✓ Elevation activated")
        click.echo(f"  Role: {data['role_name']}")
        click.echo(f"  Expires: {data['expires_at']}")
    elif response.status_code == 202:
        data = response.json()
        click.echo(f"⏳ Elevation request pending approval")
        click.echo(f"  Request ID: {data['id']}")
    else:
        click.echo(f"✗ Failed: {response.json().get('error')}")
```

### Stap 8: Keycloak Configuratie (Via Admin UI)

**8.1 Maak PIM groepen aan:**

```bash
# Via Keycloak Admin Console GUI:
# Realms → Production → Groups → Create Group

# Of via kcadm CLI:
kubectl -n auth exec -it deployment/keycloak -- /opt/keycloak/bin/kcadm.sh config credentials \
  --server http://localhost:8080 \
  --realm master \
  --user admin \
  --password changeme

kubectl -n auth exec -it deployment/keycloak -- /opt/keycloak/bin/kcadm.sh create groups \
  -r production \
  -s name=k8s-cluster-admin \
  -s 'attributes.description=["PIM-managed cluster admin access"]'

kubectl -n auth exec -it deployment/keycloak -- /opt/keycloak/bin/kcadm.sh create groups \
  -r production \
  -s name=k8s-production-read \
  -s 'attributes.description=["PIM-managed production read access"]'
```

**8.2 Haal Group IDs op (voor database config):**

```bash
# Haal group ID op voor configuratie in database
GROUP_ID=$(kubectl -n auth exec deployment/keycloak -- \
  /opt/keycloak/bin/kcadm.sh get groups -r production --fields id,name | \
  jq -r '.[] | select(.name=="k8s-cluster-admin") | .id')

echo "k8s-cluster-admin group ID: $GROUP_ID"

# Update database met correcte group ID
kubectl -n auth exec -i deployment/pim-postgres -- \
  psql -U pim -d keycloak_pim <<EOF
UPDATE pim_eligible_roles 
SET keycloak_group_id = '$GROUP_ID' 
WHERE role_name = 'k8s-cluster-admin';
EOF
```

### Stap 9: Test de Setup

```bash
# 1. Check of PIM controller draait
kubectl -n auth get pods -l app=pim-controller

# 2. Check health endpoint
kubectl -n auth port-forward svc/pim-controller 8080:80
curl http://localhost:8080/health

# 3. Request elevation via ITLC
itlc elevate --role=k8s-production-read --duration=2h --reason="Testing PIM setup"

# 4. Check active assignments
itlc whoami --show-pim

# 5. Verify in Keycloak dat user in groep zit
# Keycloak Admin Console → Users → [user] → Groups

# 6. Test Kubernetes access
kubectl get pods --all-namespaces  # Should work now

# 7. Wait for expiration (of force cleanup)
kubectl -n auth create job --from=cronjob/pim-cleanup pim-cleanup-manual

# 8. Verify access revoked
kubectl get pods --all-namespaces  # Should fail after expiration
```

## Troubleshooting

### PIM Controller kan niet connecten met Keycloak

```bash
# Check of Keycloak service bereikbaar is
kubectl -n auth exec deployment/pim-controller -- \
  curl -v http://keycloak:8080/health

# Check Keycloak admin credentials
kubectl -n auth logs deployment/pim-controller | grep "Keycloak"
```

### Group assignment werkt niet

```bash
# Check of group ID correct is
kubectl -n auth exec deployment/pim-postgres -- \
  psql -U pim -d keycloak_pim -c "SELECT role_name, keycloak_group_id FROM pim_eligible_roles;"

# Verify in Keycloak
kubectl -n auth exec deployment/keycloak -- \
  /opt/keycloak/bin/kcadm.sh get groups -r production
```

### Cleanup job werkt niet

```bash
# Check CronJob status
kubectl -n auth get cronjobs
kubectl -n auth get jobs

# Manual trigger
kubectl -n auth create job --from=cronjob/pim-cleanup test-cleanup

# Check logs
kubectl -n auth logs job/test-cleanup
```

## Productie Aanbevelingen

1. **High Availability:**
```yaml
# pim-controller deployment
spec:
  replicas: 3  # Minimaal 3 voor HA
  strategy:
    type: RollingUpdate
    rollingUpdate:
      maxUnavailable: 1
```

2. **Monitoring:**
```yaml
# Prometheus ServiceMonitor
apiVersion: monitoring.coreos.com/v1
kind: ServiceMonitor
metadata:
  name: pim-controller
spec:
  selector:
    matchLabels:
      app: pim-controller
  endpoints:
  - port: http
    path: /metrics
```

3. **Backup Database:**
```bash
# Scheduled backup van PIM database
kubectl -n auth exec deployment/pim-postgres -- \
  pg_dump -U pim keycloak_pim | gzip > pim-backup-$(date +%Y%m%d).sql.gz
```

4. **Rate Limiting:**
Voeg Nginx ingress rate limiting toe voor PIM controller endpoints.

5. **Notifications:**
Integreer Slack/Teams webhooks voor approval requests:
```python
# In pim-controller/app.py
def notify_approvers(assignment):
    webhook_url = os.getenv('SLACK_WEBHOOK_URL')
    if webhook_url:
        requests.post(webhook_url, json={
            'text': f'PIM approval needed: {assignment["username"]} → {assignment["role_name"]}'
        })
```

## Samenvatting

✅ **Je hoeft Keycloak NIET aan te passen!**
- Standaard Bitnami Helm chart blijft ongewijzigd
- Standaard Keycloak Docker image
- Alle PIM logica in separate controller

✅ **Wat je WEL nodig hebt:**
1. Separate PostgreSQL database voor PIM data
2. PIM Controller deployment (Python Flask app)
3. CronJob voor expiration cleanup
4. Keycloak groepen aanmaken (via Admin UI)
5. ITLC CLI update om met controller te praten

✅ **Voordelen van deze aanpak:**
- Eenvoudig te onderhouden
- Keycloak updates blijven simpel
- Controller kan los geschaald worden
- Werkt met elke Keycloak versie

**Geschatte implementatietijd:** 4-6 uur voor complete setup en testing.
