CREATE USER moremoney WITH PASSWORD 'moremoney123';
CREATE DATABASE moremoney_db OWNER moremoney;
GRANT ALL PRIVILEGES ON DATABASE moremoney_db TO moremoney;
