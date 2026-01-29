import { useState } from 'react'
import {
  Card,
  CardContent,
  Typography,
  Button,
  Box,
  Switch,
  FormControlLabel,
  TextField,
  Alert,
  CircularProgress,
  Stepper,
  Step,
  StepLabel,
  Chip,
  Divider,
  Grid,
} from '@mui/material'
import {
  AutoAwesome as AIIcon,
  CheckCircle as CheckIcon,
  Error as ErrorIcon,
  Description as ReportIcon,
} from '@mui/icons-material'
import axios from 'axios'

export default function ReportGenerator({ config, onReportGenerated }) {
  const [useAI, setUseAI] = useState(true)
  const [notes, setNotes] = useState('')
  const [loading, setLoading] = useState(false)
  const [result, setResult] = useState(null)
  const [activeStep, setActiveStep] = useState(0)

  const steps = ['Fetch Updates', 'Generate Report', 'Review']

  const handleGenerate = async () => {
    setLoading(true)
    setResult(null)
    setActiveStep(0)

    try {
      // Step 1: Fetching
      setActiveStep(0)
      await new Promise((resolve) => setTimeout(resolve, 500))

      // Step 2: Generating
      setActiveStep(1)
      const response = await axios.post('/api/generate', {
        use_ai: useAI,
        notes: notes.split('\n').filter((n) => n.trim()),
      })

      // Step 3: Done
      setActiveStep(2)
      setResult(response.data)

      if (response.data.success && response.data.filename) {
        onReportGenerated(response.data.filename)
      }
    } catch (error) {
      const message =
        error.response?.data?.error ||
        error.response?.data?.detail ||
        error.message
      setResult({
        success: false,
        error: typeof message === 'string' ? message : JSON.stringify(message),
      })
    } finally {
      setLoading(false)
    }
  }

  return (
    <Box>
      <Typography variant="h5" className="font-bold text-gray-800 mb-4">
        Generate Weekly Report
      </Typography>

      <Grid container spacing={3}>
        {/* Settings Card */}
        <Grid item xs={12} md={4}>
          <Card>
            <CardContent>
              <Typography variant="h6" className="font-semibold mb-4">
                ⚙️ Settings
              </Typography>

              {/* AI Enhancement Toggle */}
              <Box className="mb-4">
                <FormControlLabel
                  control={
                    <Switch
                      checked={useAI}
                      onChange={(e) => setUseAI(e.target.checked)}
                      color="primary"
                      disabled={!config?.ai_configured}
                    />
                  }
                  label={
                    <Box className="flex items-center gap-2">
                      <AIIcon className="text-purple-500" />
                      <span>Use AI Enhancement</span>
                    </Box>
                  }
                />
                {!config?.ai_configured && (
                  <Typography variant="caption" color="error" className="block ml-9">
                    AI not configured. Set GROQ_API_KEY in .env
                  </Typography>
                )}
                {config?.ai_configured && useAI && (
                  <Typography variant="caption" color="textSecondary" className="block ml-9">
                    Groq AI will format and summarize the report
                  </Typography>
                )}
              </Box>

              <Divider className="my-4" />

              {/* Additional Notes */}
              <Typography variant="subtitle2" className="font-medium mb-2">
                Additional Notes (Optional)
              </Typography>
              <TextField
                multiline
                rows={4}
                fullWidth
                placeholder="Add notes to include in the report (one per line)..."
                value={notes}
                onChange={(e) => setNotes(e.target.value)}
                variant="outlined"
                size="small"
              />

              <Divider className="my-4" />

              {/* Generate Button */}
              <Button
                variant="contained"
                size="large"
                fullWidth
                onClick={handleGenerate}
                disabled={loading || !config?.slack_configured}
                startIcon={loading ? <CircularProgress size={20} color="inherit" /> : <ReportIcon />}
              >
                {loading ? 'Generating...' : 'Generate Report'}
              </Button>

              {!config?.slack_configured && (
                <Alert severity="error" className="mt-3">
                  Slack is not configured. Please check your .env file.
                </Alert>
              )}
            </CardContent>
          </Card>
        </Grid>

        {/* Progress & Result Card */}
        <Grid item xs={12} md={8}>
          <Card className="h-full">
            <CardContent>
              {/* Stepper */}
              {loading && (
                <Box className="mb-6">
                  <Stepper activeStep={activeStep}>
                    {steps.map((label) => (
                      <Step key={label}>
                        <StepLabel>{label}</StepLabel>
                      </Step>
                    ))}
                  </Stepper>
                </Box>
              )}

              {/* Result */}
              {result && (
                <Box>
                  {result.success ? (
                    <>
                      <Alert severity="success" className="mb-4" icon={<CheckIcon />}>
                        <Typography variant="subtitle1" className="font-semibold">
                          Report Generated Successfully!
                        </Typography>
                        <Typography variant="body2">
                          Saved as: {result.filename}
                        </Typography>
                      </Alert>

                      {/* Stats */}
                      <Box className="flex gap-2 mb-4">
                        <Chip label={`${result.stats?.daily_reports || 0} daily reports`} size="small" />
                        <Chip label={`${result.stats?.status_messages || 0} messages`} size="small" />
                        <Chip label={result.date_range} size="small" color="primary" />
                      </Box>

                      {/* Report Preview */}
                      <Typography variant="subtitle2" className="font-medium mb-2">
                        Report Preview:
                      </Typography>
                      <Box
                        className="bg-gray-50 p-4 rounded-lg border border-gray-200 max-h-96 overflow-auto"
                        sx={{ fontFamily: 'monospace', fontSize: '0.85rem', whiteSpace: 'pre-wrap' }}
                      >
                        {result.report}
                      </Box>
                    </>
                  ) : (
                    <Alert severity="error" icon={<ErrorIcon />}>
                      <Typography variant="subtitle1" className="font-semibold">
                        Failed to Generate Report
                      </Typography>
                      <Typography variant="body2">{result.error}</Typography>
                    </Alert>
                  )}
                </Box>
              )}

              {/* Initial State */}
              {!loading && !result && (
                <Box className="text-center py-12">
                  <ReportIcon className="text-gray-300 mb-4" sx={{ fontSize: 80 }} />
                  <Typography variant="h6" color="textSecondary">
                    Ready to Generate
                  </Typography>
                  <Typography variant="body2" color="textSecondary">
                    Configure your settings and click "Generate Report" to start
                  </Typography>
                </Box>
              )}
            </CardContent>
          </Card>
        </Grid>
      </Grid>
    </Box>
  )
}
