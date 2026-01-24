import { useState, useEffect } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Grid,
  Button,
  Box,
  Skeleton,
  Alert,
  Chip,
} from '@mui/material'
import {
  TrendingUp as TrendingIcon,
  Description as ReportIcon,
  People as PeopleIcon,
  CalendarToday as CalendarIcon,
  PlayArrow as PlayIcon,
} from '@mui/icons-material'
import axios from 'axios'

export default function Dashboard({ config, onGenerateClick }) {
  const [preview, setPreview] = useState(null)
  const [reports, setReports] = useState([])
  const [loading, setLoading] = useState(true)

  useEffect(() => {
    fetchData()
  }, [])

  const fetchData = async () => {
    setLoading(true)
    try {
      const [previewRes, reportsRes] = await Promise.all([
        axios.get('/api/preview?days=7'),
        axios.get('/api/reports'),
      ])
      setPreview(previewRes.data)
      setReports(reportsRes.data)
    } catch (error) {
      console.error('Failed to fetch data:', error)
    } finally {
      setLoading(false)
    }
  }

  const StatCard = ({ title, value, icon: Icon, color, subtitle }) => (
    <Card className="h-full hover:shadow-lg transition-shadow">
      <CardContent>
        <Box className="flex items-center justify-between mb-2">
          <Typography color="textSecondary" variant="body2" className="font-medium">
            {title}
          </Typography>
          <Box className={`p-2 rounded-lg bg-${color}-100`}>
            <Icon className={`text-${color}-600`} />
          </Box>
        </Box>
        {loading ? (
          <Skeleton variant="text" width={80} height={40} />
        ) : (
          <Typography variant="h4" className="font-bold">
            {value}
          </Typography>
        )}
        {subtitle && (
          <Typography variant="body2" color="textSecondary" className="mt-1">
            {subtitle}
          </Typography>
        )}
      </CardContent>
    </Card>
  )

  return (
    <Box>
      {/* Welcome Section */}
      <Box className="mb-6">
        <Typography variant="h4" className="font-bold text-gray-800 mb-2">
          Welcome back! 👋
        </Typography>
        <Typography variant="body1" color="textSecondary">
          Generate and send your weekly status reports with ease.
        </Typography>
      </Box>

      {/* Quick Action */}
      <Card className="mb-6 bg-gradient-to-r from-blue-500 to-blue-700 text-white">
        <CardContent className="flex items-center justify-between py-6">
          <Box>
            <Typography variant="h5" className="font-bold mb-1">
              Ready to Generate This Week's Report?
            </Typography>
            <Typography variant="body1" className="opacity-90">
              {preview?.date_range || 'Fetch status updates from Slack and create your report'}
            </Typography>
          </Box>
          <Button
            variant="contained"
            size="large"
            onClick={onGenerateClick}
            startIcon={<PlayIcon />}
            className="bg-white text-blue-600 hover:bg-gray-100"
            sx={{ 
              backgroundColor: 'white', 
              color: '#1976d2',
              '&:hover': { backgroundColor: '#f5f5f5' }
            }}
          >
            Generate Report
          </Button>
        </CardContent>
      </Card>

      {/* Stats Grid */}
      <Grid container spacing={3} className="mb-6">
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Daily Reports"
            value={preview?.daily_reports?.length || 0}
            icon={CalendarIcon}
            color="blue"
            subtitle="This week"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Status Updates"
            value={preview?.total_updates || 0}
            icon={TrendingIcon}
            color="green"
            subtitle="From team members"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Generated Reports"
            value={reports.length}
            icon={ReportIcon}
            color="purple"
            subtitle="Total saved"
          />
        </Grid>
        <Grid item xs={12} sm={6} md={3}>
          <StatCard
            title="Recipients"
            value={(config?.recipients_to?.length || 0) + (config?.recipients_cc?.length || 0)}
            icon={PeopleIcon}
            color="orange"
            subtitle="Configured"
          />
        </Grid>
      </Grid>

      {/* Recent Activity */}
      <Grid container spacing={3}>
        {/* Daily Reports Preview */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" className="font-semibold mb-4">
                📋 This Week's Daily Reports
              </Typography>
              {loading ? (
                <Box className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} variant="rounded" height={60} />
                  ))}
                </Box>
              ) : preview?.daily_reports?.length > 0 ? (
                <Box className="space-y-3">
                  {preview.daily_reports.slice(0, 5).map((report, index) => (
                    <Box
                      key={index}
                      className="p-3 bg-gray-50 rounded-lg border border-gray-100"
                    >
                      <Box className="flex items-center justify-between mb-1">
                        <Typography variant="subtitle2" className="font-medium">
                          {new Date(report.date).toLocaleDateString('en-US', {
                            weekday: 'short',
                            month: 'short',
                            day: 'numeric',
                          })}
                        </Typography>
                        <Chip
                          size="small"
                          label={`${report.reply_count} updates`}
                          color="primary"
                          variant="outlined"
                        />
                      </Box>
                      <Typography variant="body2" color="textSecondary" className="truncate">
                        Posted by {report.posted_by}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Alert severity="info">
                  No daily reports found this week. Make sure the Slack bot is configured correctly.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Recent Reports */}
        <Grid item xs={12} md={6}>
          <Card>
            <CardContent>
              <Typography variant="h6" className="font-semibold mb-4">
                📄 Recent Reports
              </Typography>
              {loading ? (
                <Box className="space-y-3">
                  {[1, 2, 3].map((i) => (
                    <Skeleton key={i} variant="rounded" height={60} />
                  ))}
                </Box>
              ) : reports.length > 0 ? (
                <Box className="space-y-3">
                  {reports.slice(0, 5).map((report, index) => (
                    <Box
                      key={index}
                      className="p-3 bg-gray-50 rounded-lg border border-gray-100"
                    >
                      <Typography variant="subtitle2" className="font-medium">
                        {report.name}
                      </Typography>
                      <Typography variant="body2" color="textSecondary">
                        {new Date(report.created).toLocaleString()}
                      </Typography>
                    </Box>
                  ))}
                </Box>
              ) : (
                <Alert severity="info">
                  No reports generated yet. Click "Generate Report" to create your first one!
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
