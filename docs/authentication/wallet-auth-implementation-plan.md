# Ethereum Wallet Authentication Implementation Plan

## Overview
Replace current API key authentication with Web3 wallet-based authentication for better security and user experience in the blockchain-driven drawing machine.

## Current State Analysis
- **Current Auth**: Plaintext API key sent from frontend to WebSocket
- **Issues**: API keys exposed in client-side code, no proper user management
- **Security Config**: Comprehensive RBAC framework exists in `security_config.yaml`

## Implementation Phases

### Phase 1: Core Wallet Authentication
**Goal**: Replace API key auth with wallet signature verification

#### Frontend Changes (`frontend/src/`)
- Replace API key input with "Connect Wallet" button
- Add MetaMask/WalletConnect integration
- Implement signature-based authentication flow
- Handle wallet connection states and errors

#### Backend Changes
- Replace API key validation with signature verification
- Add wallet address to user session management
- Update WebSocket authentication handler
- Implement nonce generation for replay attack prevention

#### Database Schema
```sql
CREATE TABLE users (
  id SERIAL PRIMARY KEY,
  wallet_address VARCHAR(42) UNIQUE NOT NULL,
  role VARCHAR(20) DEFAULT 'viewer',
  permissions TEXT[],
  first_seen TIMESTAMP DEFAULT NOW(),
  last_login TIMESTAMP,
  is_active BOOLEAN DEFAULT true
);

CREATE TABLE auth_nonces (
  wallet_address VARCHAR(42),
  nonce VARCHAR(64),
  expires_at TIMESTAMP,
  used BOOLEAN DEFAULT false
);
```

### Phase 2: Enhanced User Management
**Goal**: Admin interface for role management

#### Admin Panel Features
- View connected wallet addresses
- Assign/modify user roles (admin, operator, viewer, guest)
- Permission management per wallet
- Activity logging and audit trail

#### Role-Based Access Control
- Implement existing `security_config.yaml` permissions
- Motor control restrictions by role
- API access limitations
- Drawing session controls

### Phase 3: Advanced Security Features
**Goal**: Production-ready security enhancements

#### Security Enhancements
- JWT tokens with wallet address as subject
- Session management and timeout
- Rate limiting per wallet address
- Failed authentication tracking and lockouts

#### Multi-Wallet Support
- Allow users to link multiple wallets
- Primary wallet designation
- Wallet recovery mechanisms

### Phase 4: Hybrid Authentication (Optional)
**Goal**: Support non-crypto users

#### Dual Authentication Methods
- Keep wallet auth as primary
- Add optional email/password for broader access
- Unified user management system
- Migration path between auth methods

## Technical Architecture

### Authentication Flow
```
1. User → "Connect Wallet" button
2. Frontend → MetaMask connection request
3. Backend → Generate unique nonce
4. User → Sign authentication message with nonce
5. Frontend → Send wallet address + signature
6. Backend → Verify signature, create JWT session
7. Frontend → Store JWT, use for subsequent requests
```

### Security Considerations
- **Nonce Management**: Prevent replay attacks
- **Message Format**: Standardized signing messages
- **Session Duration**: Configurable JWT expiry
- **Wallet Validation**: Verify signature matches address
- **Role Persistence**: Database-backed permission system

## Integration Points

### Existing Systems
- **WebSocket Handler**: `cloud/orchestrator/cloud_orchestrator.py:254`
- **Security Config**: `config/shared/security/security_config.yaml`
- **Frontend Auth**: `frontend/src/views/ManualControlView.vue:38`

### External Dependencies
- **Web3 Library**: ethers.js or web3.js for signature verification
- **Wallet Connectors**: MetaMask, WalletConnect, Coinbase Wallet
- **Database**: PostgreSQL for user and session management

## Benefits Over Current System
- ✅ No API keys exposed in frontend
- ✅ Cryptographically secure authentication
- ✅ Self-sovereign user identity
- ✅ Natural fit for blockchain-focused application
- ✅ Eliminates password management complexity
- ✅ Leverages existing RBAC framework

## Migration Strategy
1. Implement wallet auth alongside current API key system
2. Test with admin users first
3. Gradually migrate user base
4. Deprecate API key system once stable
5. Clean up legacy authentication code

## Testing Strategy
- Unit tests for signature verification
- Integration tests for wallet connection flow
- Security testing for authentication bypass attempts
- User acceptance testing with different wallet providers

## Documentation Requirements
- User guide for wallet connection
- Admin guide for role management
- Developer documentation for auth integration
- Security audit and penetration testing report

## Timeline Estimate
- **Phase 1**: 2-3 weeks (core implementation)
- **Phase 2**: 1-2 weeks (admin panel)
- **Phase 3**: 1-2 weeks (security hardening)
- **Phase 4**: 2-3 weeks (hybrid auth, optional)

**Total**: 6-10 weeks for complete implementation

## Success Metrics
- Zero API key exposures in client-side code
- 95%+ successful wallet connection rate
- Sub-3-second authentication time
- Zero authentication bypass vulnerabilities
- Positive user feedback on UX improvement

---

*This plan can be referenced and updated as implementation progresses. Each phase can be tackled independently based on priority and resources.*