{{/*
Expand the name of the chart.
*/}}
{{- define "family-link-exporter.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "family-link-exporter.fullname" -}}
{{- if .Values.fullnameOverride }}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- $name := default .Chart.Name .Values.nameOverride }}
{{- if contains $name .Release.Name }}
{{- .Release.Name | trunc 63 | trimSuffix "-" }}
{{- else }}
{{- printf "%s-%s" .Release.Name $name | trunc 63 | trimSuffix "-" }}
{{- end }}
{{- end }}
{{- end }}

{{/*
Create chart name and version as used by the chart label.
*/}}
{{- define "family-link-exporter.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "family-link-exporter.labels" -}}
helm.sh/chart: {{ include "family-link-exporter.chart" . }}
{{ include "family-link-exporter.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "family-link-exporter.selectorLabels" -}}
app.kubernetes.io/name: {{ include "family-link-exporter.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Create the name of the service account to use
*/}}
{{- define "family-link-exporter.serviceAccountName" -}}
{{- if .Values.serviceAccount.create }}
{{- default (include "family-link-exporter.fullname" .) .Values.serviceAccount.name }}
{{- else }}
{{- default "default" .Values.serviceAccount.name }}
{{- end }}
{{- end }}

{{/*
Name of the Secret holding the Google session (existing or chart-created).
*/}}
{{- define "family-link-exporter.sessionSecretName" -}}
{{- if .Values.auth.existingSecret }}
{{- .Values.auth.existingSecret }}
{{- else }}
{{- printf "%s-session" (include "family-link-exporter.fullname" .) }}
{{- end }}
{{- end }}

{{/*
True when a session credential source is configured.
*/}}
{{- define "family-link-exporter.hasSession" -}}
{{- if or .Values.auth.existingSecret .Values.auth.storageState }}true{{- end }}
{{- end }}
