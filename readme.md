# User Management System Final Project
# Michael Galanaugh IS 601 Final Project

## Introduction

As part of my fork of the professor's repo, I decided to implement RBAC for admins. This project demonstrates a complete user CRUD system with authentication, authorization, role-based access control (RBAC), audit logging, automated testing, and Docker-based deployment.

## Project Overview & Objectives

- **Practical Experience**  
  Work with a real-world codebase, collaborate via GitHub issues and pull requests, and practice professional workflows.

- **Quality Assurance**  
  Identify and resolve bugs, write thorough unit and integration tests, and enforce code quality with linters.

- **Test Coverage**  
  Achieve necessary coverage by adding tests for edge cases, error scenarios, and new functionality. Passing all tests via Pytest with 100% accuracy.

- **Feature Implementation**  
  Design, build, and document a new feature—RBAC Enhancements—to dynamically change user roles and record audit logs.

- **Industry Readiness**  
  Use Docker, GitHub Actions CI/CD, Alembic migrations, and best practices for dependency management and configuration.

## Setup Instructions

1. **Clone the repository**  
   ```bash
   git clone https://github.com/mikeygman11/user-management-system.git
   cd user-management-system

2. **Create Virtual Environment**

    ```bash
    python3.10 -m venv .venv
    source .venv/bin/activate
    pip install -r requirements.txt

3. **Alembic and PyTest**
When you run Pytest, it deletes the user table but doesn't remove the Alembic table. This can cause Alembic to get out of sync.
To resolve this, drop the Alembic table and run the migration (docker compose exec fastapi alembic upgrade head) when you want to manually test the site through http://localhost/docs.
If you change the database schema, delete the Alembic migration, the Alembic table, and the users table. Then, regenerate the migration using the command: docker compose exec fastapi alembic revision --autogenerate -m 'initial migration'.
Since there is no real user data currently, you don't need to worry about database upgrades, but Alembic is still required to install the database tables.

4. **Run Project**

Run the project:
docker compose up --build
Set up PGAdmin at localhost:5050 (see docker compose for login details)
View logs for the app: docker compose logs fastapi -f
Run tests: docker compose exec fastapi pytest

5. **Dockerhub**
Set up the project with DockerHub deployment as in previous assignments for email testing. Enable issues in settings, create the production environment, and configure your DockerHub username and token. You don't need to add MailTrap, but if you want to, you can add the values to the production environment's variables.

## Chosen Feature

I chose to implement RBAC as a part of my project. My feature enables admins to perform and CRUD operations with other users in the system.
This involved creating a new endpoint for /users/role which changes their roles. Also, this involved changes to the existing functionality.

During development and QA, the following issues were identified and have now been resolved:

- [Issue #1: Failing tests related to RBAC in pytest](https://github.com/mikeygman11/user-management-system/issues/1)  
  **Resolution:** Updated the pytest fixtures and fixed the role-check logic in the service layer so that all RBAC tests now pass.

- [Issue #3: Verification of email is not working – link is generating an error](https://github.com/mikeygman11/user-management-system/issues/3)  
  **Resolution:** Corrected the URL generation in the email verification service, improved error handling in the verification endpoint, and added unit tests to cover failure scenarios.

- [Issue #5: Authentication overrides Admin privileges – should not override an Admin or Manager (only basic user)](https://github.com/mikeygman11/user-management-system/issues/5)  
  **Resolution:** Hardened the permission checks so that only basic users can be overridden, and prevented Admin/Manager roles from being downgraded via the standard auth flow.

- [Issue #7: Implement logging for user role changes](https://github.com/mikeygman11/user-management-system/issues/7)  
  **Resolution:** Added a `RoleChangeLog` model, hooked it into the `UserService.change_role()` method, and verified that every role change is recorded with actor, timestamp, old role, and new role.

- [Issue #8: Admin updates not processing](https://github.com/mikeygman11/user-management-system/issues/8)  
  **Resolution:** Fixed a missing dependency injection in the admin role-update endpoint and added an integration test to ensure the update flow works end-to-end.

- [Issue #11: Need to add more unit tests for the role change table and the new admin role-update endpoint](https://github.com/mikeygman11/user-management-system/issues/11)  
  **Resolution:** Wrote 10+ new pytest unit and integration tests covering the role-change table operations and protected admin endpoints under both normal and error conditions.

- [Issue #12: Fix bug where alembic does not insert role changes into db](https://github.com/mikeygman11/user-management-system/issues/12)  
  **Resolution:** Corrected the Alembic migration script to create the `role_change_logs` table properly and added a post-migration check test to prevent regressions.

---

