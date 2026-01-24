import { useState, useEffect } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  List,
  ListItem,
  ListItemText,
  ListItemSecondaryAction,
  IconButton,
  Dialog,
  DialogTitle,
  DialogContent,
  DialogActions,
  Tooltip,
  Alert,
  Chip,
} from '@mui/material'
import {
  Delete as DeleteIcon,
  Email as EmailIcon,
  Visibility as ViewIcon,
  ContentCopy as CopyIcon,
  Download as DownloadIcon,
} from '@mui/icons-material'
import axios from 'axios'

export default function ReportViewer({ selectedReport, onSendEmail }) {
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)
  const [viewReport, setViewReport] = useState(null)
  const [reportContent, setReportContent] = useState('')
  const [copied, setCopied] = useState(false)

  useEffect(() => {
    fetchReports()
  }, [])

  useEffect(() => {
    if (selectedReport) {
      handleView(selectedReport)
    }
  }, [selectedReport])

  const fetchReports = async () => {
    try {
      const response = await axios.get('/api/reports')
      setReports(response.data)
    } catch (error) {
      console.error('Failed to fetch reports:', error)
    } finally {
      setLoading(false)
    }
  }

  const handleView = async (filename) => {
    try {
      const response = await axios.get(`/api/reports/${filename}`)
      setViewReport(filename)
      setReportContent(response.data.content)
    } catch (error) {
      console.error('Failed to fetch report:', error)
    }
  }

  const handleDelete = async (filename) => {
    if (!window.confirm(`Delete ${filename}?`)) return

    try {
      await axios.delete(`/api/reports/${filename}`)
      setReports(reports.filter((r) => r.name !== filename))
      if (viewReport === filename) {
        setViewReport(null)
        setReportContent('')
      }
    } catch (error) {
      console.error('Failed to delete report:', error)
    }
  }

  const handleCopy = () => {
    navigator.clipboard.writeText(reportContent)
    setCopied(true)
    setTimeout(() => setCopied(false), 2000)
  }

  const handleDownload = () => {
    const blob = new Blob([reportContent], { type: 'text/plain' })
    const url = URL.createObjectURL(blob)
    const a = document.createElement('a')
    a.href = url
    a.download = viewReport
    a.click()
    URL.revokeObjectURL(url)
  }

  return (
    <Box>
      <Typography variant="h5" className="font-bold text-gray-800 mb-4">
        Generated Reports
      </Typography>

      <Box className="grid grid-cols-1 lg:grid-cols-3 gap-4">
        {/* Reports List */}
        <Card className="lg:col-span-1">
          <CardContent>
            <Typography variant="h6" className="font-semibold mb-4">
              📄 Report Files
            </Typography>

            {reports.length === 0 ? (
              <Alert severity="info">No reports generated yet.</Alert>
            ) : (
              <List className="max-h-96 overflow-auto">
                {reports.map((report) => (
                  <ListItem
                    key={report.name}
                    button
                    selected={viewReport === report.name}
                    onClick={() => handleView(report.name)}
                    className="rounded-lg mb-1"
                  >
                    <ListItemText
                      primary={report.name}
                      secondary={new Date(report.created).toLocaleString()}
                      primaryTypographyProps={{ className: 'text-sm font-medium' }}
                      secondaryTypographyProps={{ className: 'text-xs' }}
                    />
                    <ListItemSecondaryAction>
                      <Tooltip title="Delete">
                        <IconButton
                          edge="end"
                          size="small"
                          onClick={(e) => {
                            e.stopPropagation()
                            handleDelete(report.name)
                          }}
                        >
                          <DeleteIcon fontSize="small" />
                        </IconButton>
                      </Tooltip>
                    </ListItemSecondaryAction>
                  </ListItem>
                ))}
              </List>
            )}
          </CardContent>
        </Card>

        {/* Report Content */}
        <Card className="lg:col-span-2">
          <CardContent>
            <Box className="flex items-center justify-between mb-4">
              <Typography variant="h6" className="font-semibold">
                {viewReport ? `📋 ${viewReport}` : '📋 Select a Report'}
              </Typography>

              {viewReport && (
                <Box className="flex gap-2">
                  <Tooltip title={copied ? 'Copied!' : 'Copy to clipboard'}>
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<CopyIcon />}
                      onClick={handleCopy}
                      color={copied ? 'success' : 'primary'}
                    >
                      {copied ? 'Copied!' : 'Copy'}
                    </Button>
                  </Tooltip>
                  <Tooltip title="Download">
                    <Button
                      size="small"
                      variant="outlined"
                      startIcon={<DownloadIcon />}
                      onClick={handleDownload}
                    >
                      Download
                    </Button>
                  </Tooltip>
                  <Button
                    size="small"
                    variant="contained"
                    startIcon={<EmailIcon />}
                    onClick={() => onSendEmail(viewReport)}
                  >
                    Send Email
                  </Button>
                </Box>
              )}
            </Box>

            {viewReport ? (
              <Box
                className="bg-gray-50 p-4 rounded-lg border border-gray-200 max-h-[500px] overflow-auto"
                sx={{ fontFamily: 'monospace', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}
              >
                {reportContent}
              </Box>
            ) : (
              <Box className="text-center py-16 text-gray-400">
                <ViewIcon sx={{ fontSize: 60 }} className="mb-4 opacity-50" />
                <Typography>Select a report from the list to view its contents</Typography>
              </Box>
            )}
          </CardContent>
        </Card>
      </Box>
    </Box>
  )
}
