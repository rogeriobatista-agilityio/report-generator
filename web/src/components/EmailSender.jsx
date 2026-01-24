import { useState, useEffect } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  TextField,
  Alert,
  CircularProgress,
  Chip,
  FormControl,
  InputLabel,
  Select,
  MenuItem,
  Divider,
} from '@mui/material'
import {
  Send as SendIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
} from '@mui/icons-material'
import axios from 'axios'

export default function EmailSender({ config, selectedReport }) {
  const [reports, setReports] = useState([])
  const [selected, setSelected] = useState(selectedReport || '')
  const [subject, setSubject] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [reportContent, setReportContent] = useState('')

  useEffect(() => {
    fetchReports()
  }, [])

  useEffect(() => {
    if (selectedReport) {
      setSelected(selectedReport)
      fetchReportContent(selectedReport)
    }
  }, [selectedReport])

  useEffect(() => {
    // Generate default subject
    const now = new Date()
    const week = getISOWeek(now)
    setSubject(`End of Week Update - Week ${week}, ${now.getFullYear()}`)
  }, [])

  const getISOWeek = (date) => {
    const d = new Date(date)
    d.setHours(0, 0, 0, 0)
    d.setDate(d.getDate() + 4 - (d.getDay() || 7))
    const yearStart = new Date(d.getFullYear(), 0, 1)
    return Math.ceil(((d - yearStart) / 86400000 + 1) / 7)
  }

  const fetchReports = async () => {
    try {
      const response = await axios.get('/api/reports')
      setReports(response.data)
    } catch (error) {
      console.error('Failed to fetch reports:', error)
    }
  }

  const fetchReportContent = async (filename) => {
    try {
      const response = await axios.get(`/api/reports/${filename}`)
      setReportContent(response.data.content)
    } catch (error) {
      console.error('Failed to fetch report:', error)
    }
  }

  const handleReportChange = (e) => {
    setSelected(e.target.value)
    if (e.target.value) {
      fetchReportContent(e.target.value)
    } else {
      setReportContent('')
    }
  }

  const handleSend = async () => {
    if (!selected) {
      setResult({ success: false, message: 'Please select a report' })
      return
    }

    setLoading(true)
    setResult(null)

    try {
      const response = await axios.post('/api/send-email', {
        report_file: selected,
        subject: subject,
      })
      setResult(response.data)
    } catch (error) {
      setResult({
        success: false,
        message: error.response?.data?.detail || error.message,
      })
    } finally {
      setLoading(false)
    }
  }

  const extractEmail = (recipient) => {
    const match = recipient.match(/<([^>]+)>/)
    return match ? match[1] : recipient
  }

  return (
    <Box>
      <Typography variant="h5" className="font-bold text-gray-800 mb-4">
        Send Report via Email
      </Typography>

      <Box className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Email Form */}
        <Card className="lg:col-span-1">
          <CardContent>
            <Typography variant="h6" className="font-semibold mb-4">
              📧 Email Details
            </Typography>

            {/* Email Configuration Check */}
            {!config?.email_configured && (
              <Alert severity="warning" className="mb-4">
                Email is not configured. Please set EMAIL_USERNAME and EMAIL_PASSWORD in your .env
                file.
              </Alert>
            )}

            {/* Report Selection */}
            <FormControl fullWidth className="mb-4">
              <InputLabel>Select Report</InputLabel>
              <Select value={selected} onChange={handleReportChange} label="Select Report">
                {reports.map((report) => (
                  <MenuItem key={report.name} value={report.name}>
                    {report.name}
                  </MenuItem>
                ))}
              </Select>
            </FormControl>

            {/* Subject */}
            <TextField
              fullWidth
              label="Email Subject"
              value={subject}
              onChange={(e) => setSubject(e.target.value)}
              className="mb-4"
            />

            <Divider className="my-4" />

            {/* Recipients Preview */}
            <Typography variant="subtitle2" className="font-medium mb-2">
              To:
            </Typography>
            <Box className="flex flex-wrap gap-1 mb-3">
              {config?.recipients_to?.map((r, i) => (
                <Chip key={i} label={extractEmail(r)} size="small" color="primary" />
              )) || <Typography color="textSecondary">No recipients configured</Typography>}
            </Box>

            {config?.recipients_cc?.length > 0 && (
              <>
                <Typography variant="subtitle2" className="font-medium mb-2">
                  CC:
                </Typography>
                <Box className="flex flex-wrap gap-1 mb-4">
                  {config.recipients_cc.map((r, i) => (
                    <Chip key={i} label={extractEmail(r)} size="small" variant="outlined" />
                  ))}
                </Box>
              </>
            )}

            <Divider className="my-4" />

            {/* Send Button */}
            <Button
              variant="contained"
              size="large"
              fullWidth
              onClick={handleSend}
              disabled={loading || !config?.email_configured || !selected}
              startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <SendIcon />}
              color="primary"
            >
              {loading ? 'Sending...' : 'Send Email'}
            </Button>

            {/* Result */}
            {result && (
              <Alert
                severity={result.success ? 'success' : 'error'}
                className="mt-4"
                icon={result.success ? <CheckIcon /> : <ErrorIcon />}
              >
                {result.message}
              </Alert>
            )}
          </CardContent>
        </Card>

        {/* Preview */}
        <Card className="lg:col-span-2">
          <CardContent>
            <Typography variant="h6" className="font-semibold mb-4">
              📋 Email Preview
            </Typography>

            {selected && reportContent ? (
              <>
                {/* Email Header Preview */}
                <Box className="bg-gray-100 p-4 rounded-lg mb-4">
                  <Typography variant="body2">
                    <strong>From:</strong> {config?.sender_name} &lt;{config?.sender_email}&gt;
                  </Typography>
                  <Typography variant="body2">
                    <strong>To:</strong> {config?.recipients_to?.map(extractEmail).join(', ')}
                  </Typography>
                  {config?.recipients_cc?.length > 0 && (
                    <Typography variant="body2">
                      <strong>CC:</strong> {config.recipients_cc.map(extractEmail).join(', ')}
                    </Typography>
                  )}
                  <Typography variant="body2">
                    <strong>Subject:</strong> {subject}
                  </Typography>
                </Box>

                {/* Email Body Preview */}
                <Box
                  className="bg-white p-4 rounded-lg border border-gray-200 max-h-[400px] overflow-auto"
                  sx={{ fontFamily: 'Arial, sans-serif', fontSize: '0.9rem', whiteSpace: 'pre-wrap' }}
                >
                  {reportContent}
                </Box>
              </>
            ) : (
              <Box className="text-center py-16 text-gray-400">
                <SendIcon sx={{ fontSize: 60 }} className="mb-4 opacity-50" />
                <Typography>Select a report to preview the email</Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    </Box>
  )
}
