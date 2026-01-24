import { useState, useEffect } from 'react'
import {
  AppBar,
  Toolbar,
  Typography,
  Container,
  Box,
  Tabs,
  Tab,
  Paper,
  Chip,
  IconButton,
  Tooltip,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  Description as ReportIcon,
  Email as EmailIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckIcon,
  Cancel as ErrorIcon,
} from '@mui/icons-material'
import axios from 'axios'

import Dashboard from './components/Dashboard'
import ReportGenerator from './components/ReportGenerator'
import ReportViewer from './components/ReportViewer'
import EmailSender from './components/EmailSender'
import Settings from './components/Settings'

const API_BASE = '/api'

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index} className="py-4">
      {value === index && children}
    </div>
  )
}

export default function App() {
  const [tab, setTab] = useState(0)
  const [config, setConfig] = useState(null)
  const [loading, setLoading] = useState(true)
  const [selectedReport, setSelectedReport] = useState(null)

  useEffect(() => {
    fetchConfig()
  }, [])

  const fetchConfig = async () => {
    try {
      const response = await axios.get(`${API_BASE}/config`)
      setConfig(response.data)
    } catch (error) {
      console.error('Failed to fetch config:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleReportGenerated = (filename) => {
    setSelectedReport(filename)
    setTab(2) // Switch to Reports tab
  }

  const handleSendEmail = (filename) => {
    setSelectedReport(filename)
    setTab(3) // Switch to Email tab
  }

  return (
    <Box className="min-h-screen bg-gray-50">
      {/* Header */}
      <AppBar position="static" elevation={0} className="bg-gradient-to-r from-blue-600 to-blue-800">
        <Toolbar>
          <ReportIcon className="mr-3" />
          <Typography variant="h6" component="div" className="flex-grow font-semibold">
            Weekly Report Generator
          </Typography>
          
          {/* Status indicators */}
          <div className="flex items-center gap-2 mr-4">
            {config && (
              <>
                <Tooltip title={config.slack_configured ? "Slack connected" : "Slack not configured"}>
                  <Chip
                    size="small"
                    icon={config.slack_configured ? <CheckIcon /> : <ErrorIcon />}
                    label="Slack"
                    color={config.slack_configured ? "success" : "error"}
                    variant="outlined"
                    className="bg-white/10"
                  />
                </Tooltip>
                <Tooltip title={config.ai_configured ? "AI enabled" : "AI not configured"}>
                  <Chip
                    size="small"
                    icon={config.ai_configured ? <CheckIcon /> : <ErrorIcon />}
                    label="AI"
                    color={config.ai_configured ? "success" : "warning"}
                    variant="outlined"
                    className="bg-white/10"
                  />
                </Tooltip>
                <Tooltip title={config.email_configured ? "Email configured" : "Email not configured"}>
                  <Chip
                    size="small"
                    icon={config.email_configured ? <CheckIcon /> : <ErrorIcon />}
                    label="Email"
                    color={config.email_configured ? "success" : "warning"}
                    variant="outlined"
                    className="bg-white/10"
                  />
                </Tooltip>
              </>
            )}
          </div>
        </Toolbar>
      </AppBar>

      {/* Navigation Tabs */}
      <Paper elevation={1} className="sticky top-0 z-10">
        <Container maxWidth="lg">
          <Tabs
            value={tab}
            onChange={(e, newValue) => setTab(newValue)}
            indicatorColor="primary"
            textColor="primary"
          >
            <Tab icon={<DashboardIcon />} label="Dashboard" iconPosition="start" />
            <Tab icon={<ReportIcon />} label="Generate" iconPosition="start" />
            <Tab icon={<ReportIcon />} label="Reports" iconPosition="start" />
            <Tab icon={<EmailIcon />} label="Send Email" iconPosition="start" />
            <Tab icon={<SettingsIcon />} label="Settings" iconPosition="start" />
          </Tabs>
        </Container>
      </Paper>

      {/* Main Content */}
      <Container maxWidth="lg" className="py-6">
        <TabPanel value={tab} index={0}>
          <Dashboard config={config} onGenerateClick={() => setTab(1)} />
        </TabPanel>
        
        <TabPanel value={tab} index={1}>
          <ReportGenerator 
            config={config} 
            onReportGenerated={handleReportGenerated}
          />
        </TabPanel>
        
        <TabPanel value={tab} index={2}>
          <ReportViewer 
            selectedReport={selectedReport}
            onSendEmail={handleSendEmail}
          />
        </TabPanel>
        
        <TabPanel value={tab} index={3}>
          <EmailSender 
            config={config}
            selectedReport={selectedReport}
          />
        </TabPanel>
        
        <TabPanel value={tab} index={4}>
          <Settings config={config} onConfigUpdate={fetchConfig} />
        </TabPanel>
      </Container>

      {/* Footer */}
      <Box className="py-4 text-center text-gray-500 text-sm">
        <Typography variant="body2">
          Report Generator v1.0 • Made with ❤️ for Agility Squad
        </Typography>
      </Box>
    </Box>
  )
}
