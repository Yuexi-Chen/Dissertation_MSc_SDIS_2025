import json
import requests
import os
import subprocess
import sys
import logging
import shutil
from datetime import datetime
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# SonarQube configuration
SONARQUBE_URL = 'http://localhost:9000/'
SONARQUBE_TOKEN = os.environ.get('SONAR_TOKEN') 

# Default temporary directory for SonarQube analysis
DEFAULT_TEMP_DIR = os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'results', 'sonarcube_temp_files')

def check_sonar_scanner():
    """
    Check if sonar-scanner is installed and available in PATH
    
    Returns:
        tuple: (is_available, scanner_path, error_message)
    """
    # Check if sonar-scanner is in PATH
    is_windows = sys.platform.startswith('win')
    sonar_scanner_cmd = 'sonar-scanner.bat' if is_windows else 'sonar-scanner'
    scanner_path = shutil.which(sonar_scanner_cmd)
    
    if scanner_path:
        return True, scanner_path, None
    
    # Sonar scanner not found, provide helpful error message
    error_message = (
        f"sonar-scanner not found in PATH. Please install sonar-scanner and add it to PATH.\n"
    )
    
    return False, None, error_message

class SonarQubeAnalyzer:
    """
    Class to interact with SonarQube API for code analysis
    """
    
    def __init__(self, url=SONARQUBE_URL, token=SONARQUBE_TOKEN, temp_dir=DEFAULT_TEMP_DIR):
        """
        Initialize SonarQube analyzer with URL and token
        
        Args:
            url: SonarQube URL
            token: SonarQube token
            temp_dir: Temporary directory for SonarQube analysis
        """
        self.url = url
        self.token = token
        self.session = None
        self.temp_dir = temp_dir
        
        if self.temp_dir and not os.path.exists(self.temp_dir):
            os.makedirs(self.temp_dir, exist_ok=True)
            logger.info(f"Created temporary directory: {self.temp_dir}")
        
        if not self.token:
            logger.warning("SONAR_TOKEN environment variable not set. SonarQube analysis will not work.")
    
    def authenticate(self):
        """
        Authenticate with SonarQube API using token
        """
        if not self.token:
            logger.error("Cannot authenticate: SONAR_TOKEN not set")
            return False
            
        self.session = requests.Session()
        self.session.auth = (self.token, '')
        
        try:
            # Test authentication
            logger.info(f"Authenticating with SonarQube at {self.url}...")
            response = self.session.get(f"{self.url}api/user_tokens/search")
            logger.info(f"Authentication response status code: {response.status_code}")
            
            if response.status_code != 200:
                logger.error(f"Authentication failed: {response.status_code} - {response.text}")
                return False
                
            logger.info("Authentication successful")
            return True
        except requests.exceptions.RequestException as e:
            logger.error(f"Error connecting to SonarQube: {e}")
            return False
    
    def create_project(self, project_key, project_name):
        """
        Create a new project in SonarQube
        """
        if not self.session:
            if not self.authenticate():
                return False
                
        try:
            logger.info(f"Creating project: {project_name} (key: {project_key})")
            data = {'name': project_name, 'project': project_key}
            response = self.session.post(f"{self.url}api/projects/create", data=data)
            logger.info(f"Project creation response status code: {response.status_code}")
            
            if response.status_code == 200:
                logger.info(f"Project created: {project_name}")
                return True
            elif response.status_code == 400 and "already exists" in response.text:
                logger.info(f"Project already exists: {project_name}")
                return True
            else:
                logger.warning(f"Failed to create project: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error creating project: {e}")
            return False
    
    def delete_project(self, project_key):
        """
        Delete a project from SonarQube
        """
        if not self.session:
            if not self.authenticate():
                return False
                
        try:
            logger.info(f"Deleting project: {project_key}")
            data = {'project': project_key}
            response = self.session.post(f"{self.url}api/projects/delete", data=data)
            logger.info(f"Project deletion response status code: {response.status_code}")
            
            if response.status_code == 204:
                logger.info(f"Project deleted: {project_key}")
                return True
            else:
                logger.warning(f"Failed to delete project: {response.status_code} - {response.text}")
                return False
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting project: {e}")
            return False
    
    def run_analysis(self, project_key, file_path, temp_dir=None):
        """
        Run SonarQube analysis on a file
        
        Args:
            project_key: SonarQube project key
            file_path: Path to the file to analyze
            temp_dir: Temporary directory for SonarQube analysis (overrides the instance temp_dir)
            
        Returns:
            bool: True if analysis was successful, False otherwise
        """
        if not os.path.exists(file_path):
            logger.error(f"File not found: {file_path}")
            return False
            
        # Check if sonar-scanner is available
        is_available, scanner_path, error_message = check_sonar_scanner()
        if not is_available:
            logger.error(error_message)
            return False
            
        logger.info(f"Using sonar-scanner at: {scanner_path}")
        
        file_path = os.path.abspath(file_path)
        logger.info(f"Absolute file path: {file_path}")
        
        working_temp_dir = temp_dir if temp_dir else self.temp_dir
        
        if working_temp_dir and not os.path.exists(working_temp_dir):
            os.makedirs(working_temp_dir, exist_ok=True)
            logger.info(f"Created working temporary directory: {working_temp_dir}")
        
        if working_temp_dir:
            analysis_dir = os.path.join(working_temp_dir, f"{project_key}_{datetime.now().strftime('%Y%m%d_%H%M%S')}")
            os.makedirs(analysis_dir, exist_ok=True)
            logger.info(f"Created analysis directory: {analysis_dir}")
        else:
            analysis_dir = None
        
        is_windows = sys.platform.startswith('win')
        sonar_scanner_cmd = 'sonar-scanner.bat' if is_windows else 'sonar-scanner'
        
        if is_windows:
            sonar_cmd = f"{sonar_scanner_cmd} -Dsonar.projectKey={project_key} -Dsonar.sources=\"{file_path}\""
            sonar_cmd += f" -Dsonar.host.url={self.url} -Dsonar.login={self.token}"
            
            if analysis_dir:
                sonar_cmd += f" -Dsonar.working.directory=\"{analysis_dir}\""
                
            shell = True
        else:
            sonar_cmd = [
                sonar_scanner_cmd,
                f"-Dsonar.projectKey={project_key}",
                f"-Dsonar.sources={file_path}",
                f"-Dsonar.host.url={self.url}",
                f"-Dsonar.login={self.token}"
            ]
            
            if analysis_dir:
                sonar_cmd.append(f"-Dsonar.working.directory={analysis_dir}")
                
            shell = False
            
        logger.info(f"Running SonarQube analysis for {project_key}")
        logger.info(f"Command: {sonar_cmd if not isinstance(sonar_cmd, list) else ' '.join(sonar_cmd)}")
        
        try:
            process = subprocess.Popen(
                sonar_cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                shell=shell,
                universal_newlines=True
            )
            stdout, stderr = process.communicate()
            
            if stdout:
                logger.info("sonar-scanner output:")
                for line in stdout.splitlines():
                    logger.info(f"  {line}")
            
            if stderr:
                logger.warning("sonar-scanner error output:")
                for line in stderr.splitlines():
                    logger.warning(f"  {line}")
            
            if process.returncode != 0:
                logger.error(f"SonarQube analysis failed with return code {process.returncode}")
                return False
                
            logger.info(f"SonarQube analysis completed for {project_key}")
            
            logger.info("Waiting for SonarQube to process the analysis results...")
            import time
            time.sleep(5) 
            
            return True
        except Exception as e:
            logger.error(f"Error running SonarQube analysis: {e}")
            return False
    
    def get_measures(self, project_key, metrics=None):
        """
        Get measures for a project from SonarQube
        
        Args:
            project_key: The project key in SonarQube
            metrics: List of metrics to retrieve (default: code quality metrics)
        
        Returns:
            Dictionary of metrics or None if failed
        """
        if not self.session:
            if not self.authenticate():
                return None
                
        if metrics is None:
            metrics = [
                'complexity',           
                'cognitive_complexity', 
                'comment_lines_density', 
                'duplicated_lines_density', 
                'ncloc',      
                'bugs',  
                'vulnerabilities',
                'code_smells',
                'security_rating',
                'reliability_rating',
                'sqale_rating'
            ]
            
        metrics_str = ','.join(metrics)
        
        try:
            logger.info(f"Getting measures for project: {project_key}")
            params = {'component': project_key, 'metricKeys': metrics_str}
            response = self.session.get(f"{self.url}api/measures/component", params=params)
            logger.info(f"Get measures response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                # Extract measures into a dictionary
                measures = {}
                if 'component' in data and 'measures' in data['component']:
                    for measure in data['component']['measures']:
                        measures[measure['metric']] = measure['value']
                    
                    logger.info(f"Retrieved {len(measures)} measures")
                    return measures
                else:
                    logger.warning("No measures found in response")
                    return {}
            else:
                logger.warning(f"Failed to get measures: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting measures: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing SonarQube response: {e}")
            return None
            
    def get_issues(self, project_key, severity=None, types=None):
        """
        Get issues for a project from SonarQube
        
        Args:
            project_key: The project key in SonarQube
            severity: List of severities to filter by (INFO, MINOR, MAJOR, CRITICAL, BLOCKER)
            types: List of types to filter by (BUG, VULNERABILITY, CODE_SMELL)
            
        Returns:
            List of issues or None if failed
        """
        if not self.session:
            if not self.authenticate():
                return None
                
        try:
            logger.info(f"Getting issues for project: {project_key}")
            
            # Build parameters
            params = {
                'componentKeys': project_key,
                'ps': 500  # Page size
            }
            
            if severity:
                params['severities'] = ','.join(severity) if isinstance(severity, list) else severity
                
            if types:
                params['types'] = ','.join(types) if isinstance(types, list) else types
            
            response = self.session.get(f"{self.url}api/issues/search", params=params)
            logger.info(f"Get issues response status code: {response.status_code}")
            
            if response.status_code == 200:
                data = response.json()
                
                if 'issues' in data:
                    issues = data['issues']
                    logger.info(f"Retrieved {len(issues)} issues")
                    return issues
                else:
                    logger.warning("No issues found in response")
                    return []
            else:
                logger.warning(f"Failed to get issues: {response.status_code} - {response.text}")
                return None
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting issues: {e}")
            return None
        except json.JSONDecodeError as e:
            logger.error(f"Error parsing SonarQube response: {e}")
            return None

    def delete_all_projects(self):
        """
        Delete all projects from SonarQube
        
        Returns:
            bool: True if all projects were deleted successfully, False otherwise
        """
        if not self.session:
            if not self.authenticate():
                return False
                
        try:
            logger.info("Fetching all projects from SonarQube...")
            response = self.session.get(f"{self.url}api/projects/search")
            
            if response.status_code != 200:
                logger.error(f"Failed to fetch projects: {response.status_code} - {response.text}")
                return False
            
            projects = response.json().get('components', [])
            logger.info(f"Found {len(projects)} projects to delete")
            
            success = True
            for project in projects:
                project_key = project['key']
                if not self.delete_project(project_key):
                    logger.warning(f"Failed to delete project: {project_key}")
                    success = False
            
            return success
            
        except requests.exceptions.RequestException as e:
            logger.error(f"Error deleting all projects: {e}")
            return False

def test_sonarqube_connection():
    """
    Test if SonarQube is accessible and API token is valid
    """
    logger.info("Testing SonarQube connection...")
    analyzer = SonarQubeAnalyzer()
    if analyzer.authenticate():
        logger.info("SonarQube connection successful")
        return True
    else:
        logger.error("SonarQube connection failed")
        return False

if __name__ == '__main__':
    # Test SonarQube connection
    test_sonarqube_connection() 