{{/*
Expand the name of the chart.
*/}}
{{- define "accountabilidash.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Create a default fully qualified app name.
*/}}
{{- define "accountabilidash.fullname" -}}
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
{{- define "accountabilidash.chart" -}}
{{- printf "%s-%s" .Chart.Name .Chart.Version | replace "+" "_" | trunc 63 | trimSuffix "-" }}
{{- end }}

{{/*
Common labels
*/}}
{{- define "accountabilidash.labels" -}}
helm.sh/chart: {{ include "accountabilidash.chart" . }}
{{ include "accountabilidash.selectorLabels" . }}
{{- if .Chart.AppVersion }}
app.kubernetes.io/version: {{ .Chart.AppVersion | quote }}
{{- end }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
{{- end }}

{{/*
Selector labels
*/}}
{{- define "accountabilidash.selectorLabels" -}}
app.kubernetes.io/name: {{ include "accountabilidash.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end }}

{{/*
Component-specific labels
*/}}
{{- define "accountabilidash.backend.labels" -}}
{{ include "accountabilidash.labels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{- define "accountabilidash.backend.selectorLabels" -}}
{{ include "accountabilidash.selectorLabels" . }}
app.kubernetes.io/component: backend
{{- end }}

{{- define "accountabilidash.frontend.labels" -}}
{{ include "accountabilidash.labels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{- define "accountabilidash.frontend.selectorLabels" -}}
{{ include "accountabilidash.selectorLabels" . }}
app.kubernetes.io/component: frontend
{{- end }}

{{- define "accountabilidash.postgres.labels" -}}
{{ include "accountabilidash.labels" . }}
app.kubernetes.io/component: database
{{- end }}

{{- define "accountabilidash.postgres.selectorLabels" -}}
{{ include "accountabilidash.selectorLabels" . }}
app.kubernetes.io/component: database
{{- end }}

{{/*
Backend image. When imageRegistry and imageOwner are set (e.g. ghcr.io), uses
ghcr.io/owner/accountabilidash-backend:tag. Otherwise uses repository:tag.
*/}}
{{- define "accountabilidash.backend.image" -}}
{{- $registry := .Values.global.imageRegistry -}}
{{- $owner := .Values.global.imageOwner -}}
{{- $repository := .Values.backend.image.repository -}}
{{- $tag := .Values.backend.image.tag | default .Chart.AppVersion -}}
{{- if and $registry $owner }}
{{- printf "%s/%s/%s:%s" $registry $owner $repository $tag -}}
{{- else if $registry }}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- else }}
{{- printf "%s:%s" $repository $tag -}}
{{- end }}
{{- end }}

{{/*
Frontend image. Same logic as backend.
*/}}
{{- define "accountabilidash.frontend.image" -}}
{{- $registry := .Values.global.imageRegistry -}}
{{- $owner := .Values.global.imageOwner -}}
{{- $repository := .Values.frontend.image.repository -}}
{{- $tag := .Values.frontend.image.tag | default .Chart.AppVersion -}}
{{- if and $registry $owner }}
{{- printf "%s/%s/%s:%s" $registry $owner $repository $tag -}}
{{- else if $registry }}
{{- printf "%s/%s:%s" $registry $repository $tag -}}
{{- else }}
{{- printf "%s:%s" $repository $tag -}}
{{- end }}
{{- end }}
