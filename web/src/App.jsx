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
  Tooltip,
  CircularProgress,
} from '@mui/material'
import {
  Dashboard as DashboardIcon,
  Description as ReportIcon,
  Email as EmailIcon,
  Settings as SettingsIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Chat as SlackIcon,
  Psychology as AIIcon,
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

function StatusIndicator({ configured, label, icon: Icon, loading }) {
  if (loading) {
    return (
      <div className="flex items-center gap-1.5 px-3 py-1.5 rounded-full bg-white/20">
        <CircularProgress size={14} sx={{ color: 'white' }} />
        <span className="text-xs font-medium text-white/80">{label}</span>
      </div>
    )
  }

  return (
    <Tooltip 
      title={configured ? `${label} connected` : `${label} not configured`}
      arrow
    >
      <div 
        className={`flex items-center gap-1.5 px-3 py-1.5 rounded-full transition-all cursor-default ${
          configured 
            ? 'bg-white text-gray-800 shadow-md' 
            : 'bg-white/20 text-white/70'
        }`}
      >
        <Icon 
          sx={{ 
            fontSize: 16,
            color: configured ? '#16a34a' : 'inherit'
          }} 
        />
        <span className="text-xs font-semibold">
          {label}
        </span>
        {configured ? (
          <CheckIcon sx={{ fontSize: 14, color: '#16a34a' }} />
        ) : (
          <ErrorIcon sx={{ fontSize: 14, color: '#f59e0b' }} />
        )}
      </div>
    </Tooltip>
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
      <AppBar 
        position="static" 
        elevation={0} 
        sx={{ 
          background: 'linear-gradient(135deg, #1e40af 0%, #3b82f6 50%, #0ea5e9 100%)',
        }}
      >
        <Toolbar className="px-4 md:px-6">
          {/* Logo & Title */}
          <Box className="flex items-center gap-3">
            <Box 
              className="flex items-center justify-center w-10 h-10 rounded-xl bg-white/20 backdrop-blur"
            >
              <ReportIcon className="text-white" />
            </Box>
            <Box>
              <Typography 
                variant="h6" 
                component="div" 
                className="font-bold text-white leading-tight"
              >
                Weekly Report Generator
              </Typography>
              <Typography 
                variant="caption" 
                className="text-blue-200 hidden sm:block"
              >
                Agility Squad
              </Typography>
            </Box>
          </Box>
          
          {/* Spacer */}
          <Box className="flex-grow" />
          
          {/* Status Indicators */}
          <Box className="flex items-center gap-2">
            <StatusIndicator 
              configured={config?.slack_configured} 
              label="Slack" 
              icon={SlackIcon}
              loading={loading}
            />
            <StatusIndicator 
              configured={config?.ai_configured} 
              label="AI" 
              icon={AIIcon}
              loading={loading}
            />
            <StatusIndicator 
              configured={config?.email_configured} 
              label="Email" 
              icon={EmailIcon}
              loading={loading}
            />
          </Box>
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
            variant="scrollable"
            scrollButtons="auto"
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
