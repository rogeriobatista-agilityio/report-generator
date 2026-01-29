import { useState, useEffect } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Alert,
  CircularProgress,
  Chip,
  List,
  ListItem,
  ListItemIcon,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Divider,
  TextField,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Switch,
  Tabs,
  Tab,
  InputAdornment,
  Snackbar,
} from '@mui/material'
import {
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Refresh as RefreshIcon,
  Chat as SlackIcon,
  Email as EmailIcon,
  Psychology as AIIcon,
  Person as PersonIcon,
  Add as AddIcon,
  Delete as DeleteIcon,
  Edit as EditIcon,
  Upload as ImportIcon,
  Visibility as VisibilityIcon,
  VisibilityOff as VisibilityOffIcon,
  Save as SaveIcon,
  Settings as SettingsIcon,
} from '@mui/icons-material'
import axios from 'axios'

function TabPanel({ children, value, index }) {
  return (
    <div hidden={value !== index}>
      {value === index && <Box className="py-4">{children}</Box>}
    </div>
  )
}

export default function Settings({ config, onConfigUpdate }) {
  const [tab, setTab] = useState(0)
  const [testing, setTesting] = useState({})
  const [testResults, setTestResults] = useState({})
  const [recipients, setRecipients] = useState([])
  const [settings, setSettings] = useState({})
  const [loading, setLoading] = useState(true)
  const [saving, setSaving] = useState(false)
  
  // Form state for editable settings
  const [editedSettings, setEditedSettings] = useState({})
  const [showSecrets, setShowSecrets] = useState({})
  const [hasChanges, setHasChanges] = useState(false)
  
  // Dialog state for recipients
  const [dialogOpen, setDialogOpen] = useState(false)
  const [editingRecipient, setEditingRecipient] = useState(null)
  const [recipientForm, setRecipientForm] = useState({ email: '', name: '', type: 'to' })

  // Save feedback
  const [snackbar, setSnackbar] = useState({ open: false, message: '', severity: 'success' })

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [recipientsRes, settingsRes] = await Promise.all([
        axios.get('/api/recipients'),
        axios.get('/api/settings/raw'),
      ])
      setRecipients(recipientsRes.data.recipients || [])
      const fetchedSettings = settingsRes.data.settings || {}
      setSettings(fetchedSettings)
      setEditedSettings(fetchedSettings)
      setHasChanges(false)
    } catch (error) {
      console.error('Failed to fetch data:', error)
      // Fallback to masked settings
      try {
        const settingsRes = await axios.get('/api/settings')
        setSettings(settingsRes.data.settings || {})
        setEditedSettings(settingsRes.data.settings || {})
      } catch (e) {
        console.error('Failed to fetch masked settings:', e)
      }
    } finally {
      setLoading(false)
    }
  }

  const handleSettingChange = (key, value) => {
    setEditedSettings(prev => ({ ...prev, [key]: value }))
    setHasChanges(true)
  }

  const handleSaveSettings = async () => {
    setSaving(true)
    setSnackbar(prev => ({ ...prev, open: false }))
    try {
      let saved = 0
      for (const [key, value] of Object.entries(editedSettings)) {
        if (value !== settings[key]) {
          await axios.put(`/api/settings/${key}`, { value: value || '' })
          saved += 1
        }
      }
      setSettings(editedSettings)
      setHasChanges(false)
      onConfigUpdate()
      setSnackbar({
        open: true,
        message: saved > 0 ? 'Settings saved to database.' : 'No changes to save.',
        severity: saved > 0 ? 'success' : 'info',
      })
    } catch (error) {
      console.error('Failed to save settings:', error)
      setSnackbar({
        open: true,
        message: error.response?.data?.detail || error.message || 'Failed to save settings.',
        severity: 'error',
      })
    } finally {
      setSaving(false)
    }
  }

  const testSlack = async () => {
    setTesting({ ...testing, slack: true })
    try {
      const response = await axios.post('/api/test-slack')
      setTestResults({ ...testResults, slack: response.data })
    } catch (error) {
      setTestResults({
        ...testResults,
        slack: { success: false, message: error.message },
      })
    } finally {
      setTesting({ ...testing, slack: false })
    }
  }

  const testEmail = async () => {
    setTesting({ ...testing, email: true })
    try {
      const response = await axios.post('/api/test-email')
      setTestResults({ ...testResults, email: response.data })
    } catch (error) {
      setTestResults({
        ...testResults,
        email: { success: false, message: error.message },
      })
    } finally {
      setTesting({ ...testing, email: false })
    }
  }

  const importFromEnv = async () => {
    try {
      const response = await axios.post('/api/settings/import-env')
      if (response.data.success) {
        fetchData()
        onConfigUpdate()
      }
    } catch (error) {
      console.error('Failed to import:', error)
    }
  }

  const toggleShowSecret = (key) => {
    setShowSecrets(prev => ({ ...prev, [key]: !prev[key] }))
  }

  // Recipient management
  const openAddDialog = () => {
    setEditingRecipient(null)
    setRecipientForm({ email: '', name: '', type: 'to' })
    setDialogOpen(true)
  }

  const openEditDialog = (recipient) => {
    setEditingRecipient(recipient)
    setRecipientForm({
      email: recipient.email,
      name: recipient.name || '',
      type: recipient.type,
    })
    setDialogOpen(true)
  }

  const handleSaveRecipient = async () => {
    try {
      if (editingRecipient) {
        await axios.put(`/api/recipients/${editingRecipient.id}`, recipientForm)
      } else {
        await axios.post('/api/recipients', recipientForm)
      }
      setDialogOpen(false)
      fetchData()
      onConfigUpdate()
    } catch (error) {
      console.error('Failed to save recipient:', error)
    }
  }

  const handleDeleteRecipient = async (id) => {
    if (!window.confirm('Delete this recipient?')) return
    try {
      await axios.delete(`/api/recipients/${id}`)
      fetchData()
      onConfigUpdate()
    } catch (error) {
      console.error('Failed to delete recipient:', error)
    }
  }

  const handleToggleActive = async (recipient) => {
    try {
      await axios.put(`/api/recipients/${recipient.id}`, {
        active: !recipient.active,
      })
      fetchData()
      onConfigUpdate()
    } catch (error) {
      console.error('Failed to toggle recipient:', error)
    }
  }

  const StatusChip = ({ configured, label }) => (
    <Chip
      icon={configured ? <CheckIcon /> : <ErrorIcon />}
      label={label}
      color={configured ? 'success' : 'error'}
      size="small"
    />
  )

  const SecretTextField = ({ label, settingKey, placeholder, helperText }) => {
    const isSecret = ['slack_bot_token', 'groq_api_key', 'email_password'].includes(settingKey)
    const showValue = showSecrets[settingKey]
    
    return (
      <TextField
        fullWidth
        label={label}
        type={isSecret && !showValue ? 'password' : 'text'}
        value={editedSettings[settingKey] || ''}
        onChange={(e) => handleSettingChange(settingKey, e.target.value)}
        placeholder={placeholder}
        helperText={helperText}
        size="small"
        className="mb-4"
        InputProps={isSecret ? {
          endAdornment: (
            <InputAdornment position="end">
              <IconButton onClick={() => toggleShowSecret(settingKey)} edge="end" size="small">
                {showValue ? <VisibilityOffIcon /> : <VisibilityIcon />}
              </IconButton>
            </InputAdornment>
          ),
        } : undefined}
      />
    )
  }

  const toRecipients = recipients.filter((r) => r.type === 'to')
  const ccRecipients = recipients.filter((r) => r.type === 'cc')

  return (
    <Box>
      <Box className="flex items-center justify-between mb-4 flex-wrap gap-2">
        <Box>
          <Typography variant="h5" className="font-bold text-gray-800">
            Settings & Configuration
          </Typography>
          <Typography variant="body2" color="textSecondary" className="mt-1">
            All settings are stored in the SQLite database. Edit the fields below and click Save to persist.
          </Typography>
        </Box>
        <Button
          variant="contained"
          color="primary"
          startIcon={saving ? <CircularProgress size={16} color="inherit" /> : <SaveIcon />}
          onClick={handleSaveSettings}
          disabled={saving}
          sx={{ flexShrink: 0 }}
        >
          {saving ? 'Saving…' : 'Save to database'}
        </Button>
      </Box>

      {hasChanges && (
        <Alert severity="info" className="mb-4" onClose={() => setHasChanges(false)}>
          You have unsaved changes. Click &quot;Save to database&quot; to store them.
        </Alert>
      )}

      <Tabs value={tab} onChange={(e, v) => setTab(v)} className="mb-4">
        <Tab label="Slack" icon={<SlackIcon />} iconPosition="start" />
        <Tab label="AI (Groq)" icon={<AIIcon />} iconPosition="start" />
        <Tab label="Email & SMTP" icon={<EmailIcon />} iconPosition="start" />
        <Tab label="Recipients" icon={<PersonIcon />} iconPosition="start" />
      </Tabs>

      {/* Tab 0: Slack Configuration */}
      <TabPanel value={tab} index={0}>
        <Card>
          <CardContent>
            <Box className="flex items-center justify-between mb-4">
              <Box className="flex items-center gap-2">
                <SlackIcon className="text-purple-500" />
                <Typography variant="h6" className="font-semibold">
                  Slack Configuration
                </Typography>
              </Box>
              <StatusChip
                configured={config?.slack_configured}
                label={config?.slack_configured ? 'Connected' : 'Not Configured'}
              />
            </Box>

            <Typography variant="body2" color="textSecondary" className="mb-4">
              Configure your Slack Bot to read daily status updates from your channel.
            </Typography>

            <Box className="space-y-4">
              <SecretTextField
                label="Slack Bot Token"
                settingKey="slack_bot_token"
                placeholder="xoxb-..."
                helperText="Your Slack Bot User OAuth Token (starts with xoxb-)"
              />
              
              <TextField
                fullWidth
                label="Slack Channel ID"
                value={editedSettings.slack_channel_id || ''}
                onChange={(e) => handleSettingChange('slack_channel_id', e.target.value)}
                placeholder="C0123456789"
                helperText="The channel ID where daily reports are posted (e.g., C0AAL6G0T8D)"
                size="small"
              />
            </Box>

            <Divider className="my-4" />

            <Box className="flex gap-2">
              <Button
                variant="outlined"
                onClick={testSlack}
                disabled={testing.slack}
                startIcon={testing.slack ? <CircularProgress size={16} /> : <RefreshIcon />}
              >
                Test Connection
              </Button>
            </Box>

            {testResults.slack && (
              <Alert severity={testResults.slack.success ? 'success' : 'error'} className="mt-3">
                {testResults.slack.success ? (
                  <>
                    Connected as <strong>{testResults.slack.bot_name}</strong> to{' '}
                    <strong>#{testResults.slack.channel}</strong>
                  </>
                ) : (
                  testResults.slack.message
                )}
              </Alert>
            )}

            <Alert severity="info" className="mt-4">
              <strong>How to get your Slack Bot Token:</strong>
              <ol className="mt-2 ml-4 list-decimal">
                <li>Go to <a href="https://api.slack.com/apps" target="_blank" rel="noopener" className="text-blue-600 underline">api.slack.com/apps</a></li>
                <li>Select your app or create a new one</li>
                <li>Go to "OAuth & Permissions"</li>
                <li>Copy the "Bot User OAuth Token" (starts with xoxb-)</li>
              </ol>
            </Alert>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Tab 1: AI Configuration */}
      <TabPanel value={tab} index={1}>
        <Card>
          <CardContent>
            <Box className="flex items-center justify-between mb-4">
              <Box className="flex items-center gap-2">
                <AIIcon className="text-blue-500" />
                <Typography variant="h6" className="font-semibold">
                  AI Configuration (Groq)
                </Typography>
              </Box>
              <StatusChip
                configured={config?.ai_configured}
                label={config?.ai_configured ? 'Enabled' : 'Not Configured'}
              />
            </Box>

            <Typography variant="body2" color="textSecondary" className="mb-4">
              Groq AI is used to intelligently format, categorize, and summarize your weekly reports.
            </Typography>

            <Box className="space-y-4">
              <SecretTextField
                label="Groq API Key"
                settingKey="groq_api_key"
                placeholder="gsk_..."
                helperText="Your Groq API key for AI-powered report enhancement"
              />
            </Box>

            <Alert severity="info" className="mt-4">
              <strong>How to get your Groq API Key:</strong>
              <ol className="mt-2 ml-4 list-decimal">
                <li>Go to <a href="https://console.groq.com/keys" target="_blank" rel="noopener" className="text-blue-600 underline">console.groq.com/keys</a></li>
                <li>Sign in or create an account</li>
                <li>Click "Create API Key"</li>
                <li>Copy the generated key</li>
              </ol>
            </Alert>

            {!config?.ai_configured && (
              <Alert severity="warning" className="mt-4">
                AI enhancement is optional. Reports can still be generated without it, but they won't be as well formatted.
              </Alert>
            )}
          </CardContent>
        </Card>
      </TabPanel>

      {/* Tab 2: Email & SMTP Configuration */}
      <TabPanel value={tab} index={2}>
        <Card>
          <CardContent>
            <Box className="flex items-center justify-between mb-4">
              <Box className="flex items-center gap-2">
                <EmailIcon className="text-green-500" />
                <Typography variant="h6" className="font-semibold">
                  Email & SMTP Configuration
                </Typography>
              </Box>
              <StatusChip
                configured={config?.email_configured}
                label={config?.email_configured ? 'Configured' : 'Not Configured'}
              />
            </Box>

            <Typography variant="body2" color="textSecondary" className="mb-4">
              Configure email settings to send reports directly to your team.
            </Typography>

            {/* Sender Info */}
            <Typography variant="subtitle2" className="font-medium mb-2 text-gray-700">
              Sender Information
            </Typography>
            <Box className="space-y-4 mb-6">
              <TextField
                fullWidth
                label="Sender Name"
                value={editedSettings.sender_name || ''}
                onChange={(e) => handleSettingChange('sender_name', e.target.value)}
                placeholder="Weekly Report Bot"
                helperText="The name that will appear in the From field"
                size="small"
              />
              
              <TextField
                fullWidth
                label="Sender Email"
                type="email"
                value={editedSettings.sender_email || ''}
                onChange={(e) => handleSettingChange('sender_email', e.target.value)}
                placeholder="reports@yourcompany.com"
                helperText="The email address that will appear in the From field"
                size="small"
              />
            </Box>

            <Divider className="my-4" />

            {/* SMTP Settings */}
            <Typography variant="subtitle2" className="font-medium mb-2 text-gray-700">
              SMTP Settings
            </Typography>
            <Box className="space-y-4">
              <FormControl fullWidth size="small">
                <InputLabel>Email Provider</InputLabel>
                <Select
                  value={editedSettings.email_provider || 'gmail'}
                  label="Email Provider"
                  onChange={(e) => handleSettingChange('email_provider', e.target.value)}
                >
                  <MenuItem value="gmail">Gmail</MenuItem>
                  <MenuItem value="outlook">Outlook / Office 365</MenuItem>
                  <MenuItem value="yahoo">Yahoo</MenuItem>
                  <MenuItem value="custom">Custom SMTP</MenuItem>
                </Select>
              </FormControl>
              
              <TextField
                fullWidth
                label="Email Username"
                value={editedSettings.email_username || ''}
                onChange={(e) => handleSettingChange('email_username', e.target.value)}
                placeholder="your.email@gmail.com"
                helperText="Your email address for SMTP authentication"
                size="small"
              />
              
              <SecretTextField
                label="Email Password / App Password"
                settingKey="email_password"
                placeholder="xxxx xxxx xxxx xxxx"
                helperText="For Gmail, use an App Password (not your regular password)"
              />
            </Box>

            <Divider className="my-4" />

            <Box className="flex gap-2">
              <Button
                variant="outlined"
                onClick={testEmail}
                disabled={testing.email || !editedSettings.email_username}
                startIcon={testing.email ? <CircularProgress size={16} /> : <RefreshIcon />}
              >
                Test Connection
              </Button>
            </Box>

            {testResults.email && (
              <Alert severity={testResults.email.success ? 'success' : 'error'} className="mt-3">
                {testResults.email.message}
              </Alert>
            )}

            <Alert severity="info" className="mt-4">
              <strong>Gmail App Password Setup:</strong>
              <ol className="mt-2 ml-4 list-decimal">
                <li>Enable 2-Factor Authentication on your Google account</li>
                <li>Go to <a href="https://myaccount.google.com/apppasswords" target="_blank" rel="noopener" className="text-blue-600 underline">myaccount.google.com/apppasswords</a></li>
                <li>Create a new App Password for "Mail"</li>
                <li>Use the 16-character password generated</li>
              </ol>
            </Alert>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Tab 3: Recipients */}
      <TabPanel value={tab} index={3}>
        <Card>
          <CardContent>
            <Box className="flex items-center justify-between mb-4">
              <Typography variant="h6" className="font-semibold">
                Email Recipients
              </Typography>
              <Button variant="contained" startIcon={<AddIcon />} onClick={openAddDialog}>
                Add Recipient
              </Button>
            </Box>

            {/* TO Recipients */}
            <Typography variant="subtitle2" className="font-medium mb-2 text-blue-600">
              TO Recipients (Primary)
            </Typography>
            {toRecipients.length === 0 ? (
              <Alert severity="info" className="mb-4">
                No TO recipients configured. Add recipients to send reports.
              </Alert>
            ) : (
              <List className="mb-4">
                {toRecipients.map((recipient) => (
                  <ListItem
                    key={recipient.id}
                    className={`rounded-lg mb-1 ${!recipient.active ? 'opacity-50' : ''}`}
                    sx={{ bgcolor: 'grey.50' }}
                  >
                    <ListItemIcon>
                      <PersonIcon color={recipient.active ? 'primary' : 'disabled'} />
                    </ListItemIcon>
                    <ListItemText
                      primary={recipient.name || recipient.email}
                      secondary={recipient.name ? recipient.email : null}
                    />
                    <ListItemSecondaryAction>
                      <Switch
                        size="small"
                        checked={recipient.active}
                        onChange={() => handleToggleActive(recipient)}
                      />
                      <IconButton size="small" onClick={() => openEditDialog(recipient)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleDeleteRecipient(recipient.id)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            )}

            <Divider className="my-4" />

            {/* CC Recipients */}
            <Typography variant="subtitle2" className="font-medium mb-2 text-gray-600">
              CC Recipients (Copy)
            </Typography>
            {ccRecipients.length === 0 ? (
              <Alert severity="info">No CC recipients configured.</Alert>
            ) : (
              <List>
                {ccRecipients.map((recipient) => (
                  <ListItem
                    key={recipient.id}
                    className={`rounded-lg mb-1 ${!recipient.active ? 'opacity-50' : ''}`}
                    sx={{ bgcolor: 'grey.50' }}
                  >
                    <ListItemIcon>
                      <PersonIcon color={recipient.active ? 'action' : 'disabled'} />
                    </ListItemIcon>
                    <ListItemText
                      primary={recipient.name || recipient.email}
                      secondary={recipient.name ? recipient.email : null}
                    />
                    <ListItemSecondaryAction>
                      <Switch
                        size="small"
                        checked={recipient.active}
                        onChange={() => handleToggleActive(recipient)}
                      />
                      <IconButton size="small" onClick={() => openEditDialog(recipient)}>
                        <EditIcon fontSize="small" />
                      </IconButton>
                      <IconButton size="small" onClick={() => handleDeleteRecipient(recipient.id)}>
                        <DeleteIcon fontSize="small" />
                      </IconButton>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            )}

            <Divider className="my-4" />

            {/* Import from .env */}
            <Box className="flex items-center gap-4">
              <Button variant="outlined" onClick={importFromEnv} startIcon={<ImportIcon />}>
                Import from .env
              </Button>
              <Typography variant="body2" color="textSecondary">
                Import recipients and settings from your .env file
              </Typography>
            </Box>
          </CardContent>
        </Card>
      </TabPanel>

      {/* Add/Edit Recipient Dialog */}
      <Dialog open={dialogOpen} onClose={() => setDialogOpen(false)} maxWidth="sm" fullWidth>
        <DialogTitle>{editingRecipient ? 'Edit Recipient' : 'Add Recipient'}</DialogTitle>
        <DialogContent>
          <Box className="space-y-4 pt-2">
            <TextField
              fullWidth
              label="Email Address"
              type="email"
              value={recipientForm.email}
              onChange={(e) => setRecipientForm({ ...recipientForm, email: e.target.value })}
              required
            />
            <TextField
              fullWidth
              label="Display Name (optional)"
              value={recipientForm.name}
              onChange={(e) => setRecipientForm({ ...recipientForm, name: e.target.value })}
            />
            <FormControl fullWidth>
              <InputLabel>Type</InputLabel>
              <Select
                value={recipientForm.type}
                label="Type"
                onChange={(e) => setRecipientForm({ ...recipientForm, type: e.target.value })}
              >
                <MenuItem value="to">TO (Primary)</MenuItem>
                <MenuItem value="cc">CC (Copy)</MenuItem>
              </Select>
            </FormControl>
          </Box>
        </DialogContent>
        <DialogActions>
          <Button onClick={() => setDialogOpen(false)}>Cancel</Button>
          <Button
            variant="contained"
            onClick={handleSaveRecipient}
            disabled={!recipientForm.email}
          >
            {editingRecipient ? 'Update' : 'Add'}
          </Button>
        </DialogActions>
      </Dialog>

      {/* Save feedback */}
      <Snackbar
        open={snackbar.open}
        autoHideDuration={5000}
        onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
        anchorOrigin={{ vertical: 'bottom', horizontal: 'center' }}
      >
        <Alert
          severity={snackbar.severity}
          onClose={() => setSnackbar(prev => ({ ...prev, open: false }))}
        >
          {snackbar.message}
        </Alert>
      </Snackbar>

      {/* Refresh Button */}
      <Box className="mt-6 text-center">
        <Button
          variant="outlined"
          startIcon={<RefreshIcon />}
          onClick={() => {
            fetchData()
            onConfigUpdate()
          }}
        >
          Refresh Configuration
        </Button>
      </Box>
    </Box>
  )
}
