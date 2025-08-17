markdown# Drawing Machine Configuration



Complete configuration management for the blockchain drawing machine project.



\## Directory Structure

config/

├── development/

│   └── .env.development

├── staging/

│   └── .env.staging

├── production/

│   └── .env.production.template

├── shared/

│   ├── motor/

│   │   └── motor\_mappings.yaml

│   ├── blockchain/

│   │   ├── api\_endpoints.yaml

│   │   └── service\_apis.yaml

│   ├── logging/

│   │   └── logging\_config.yaml

│   ├── monitoring/

│   │   ├── prometheus\_config.yaml

│   │   └── alert\_rules.yaml

│   └── security/

│       └── security\_config.yaml

├── templates/

├── config\_manager.py

└── README.md



\## Quick Start Commands



\### Validate All Configurations

python config\_manager.py validate



\### List All Configuration Files

python config\_manager.py list



\### View Motor Configuration

python config\_manager.py motor



\### View API Configuration

python config\_manager.py api



\## Configuration Files Overview



\### Motor Configuration

\- File: shared/motor/motor\_mappings.yaml

\- Contains: Motor specs, data mappings, operational modes

\- Purpose: Controls how blockchain data drives motor velocities



\### Blockchain APIs

\- File: shared/blockchain/api\_endpoints.yaml

\- Contains: External API settings for Coinbase, Ethereum RPC, Beacon Chain

\- Purpose: Configures data sources for drawing



\### Service APIs

\- File: shared/blockchain/service\_apis.yaml

\- Contains: Internal service endpoints and communication

\- Purpose: Service discovery and inter-service communication



\### Environment Variables

\- Development: .env.development (ready to use)

\- Staging: .env.staging (testing environment)

\- Production: .env.production.template (copy and customize)



\### Logging Configuration

\- File: shared/logging/logging\_config.yaml

\- Contains: Structured logging setup for all services

\- Purpose: Centralized logging with rotation and filtering



\### Monitoring Configuration

\- Files: shared/monitoring/prometheus\_config.yaml and alert\_rules.yaml

\- Contains: Metrics collection and alerting rules

\- Purpose: System monitoring and health checks



\### Security Configuration

\- File: shared/security/security\_config.yaml

\- Contains: Authentication, authorization, and security policies

\- Purpose: Secure access control and data protection



\## Operational Modes



1\. Blockchain Mode: Real-time Ethereum data drives motors

2\. Manual Mode: Direct user control via dashboard

3\. Offline Mode: Execute pre-computed sequences

4\. Hybrid Mode: Blockchain data with manual overrides



\## Critical Alerts Configured



\- Motor controller service down

\- Emergency stop triggered

\- High motor command failure rate

\- Blockchain data staleness

\- API failure rates

\- Low data quality scores



\## Development Setup



1\. Use development environment file

2\. Start Docker services

3\. Validate configuration with script



\## Production Deployment



1\. Copy production template

2\. Update all CHANGE\_THIS placeholders

3\. Set strong passwords and API keys

4\. Validate production configuration



\## Integration Points



\- Motor Controller: TCP communication on port 8765

\- Docker Services: PostgreSQL, Redis, Prometheus, Grafana

\- Web Dashboard: CORS and API settings

\- Blockchain APIs: Rate limiting and fallbacks

\- Monitoring: Metrics and alerting

