{{- define "incident-pulse.name" -}}
{{- default .Chart.Name .Values.nameOverride | trunc 63 | trimSuffix "-" -}}
{{- end -}}

{{- define "incident-pulse.fullname" -}}
{{- if .Values.fullnameOverride -}}
{{- .Values.fullnameOverride | trunc 63 | trimSuffix "-" -}}
{{- else if contains (include "incident-pulse.name" .) .Release.Name -}}
{{- .Release.Name | trunc 63 | trimSuffix "-" -}}
{{- else -}}
{{- printf "%s-%s" .Release.Name (include "incident-pulse.name" .) | trunc 63 | trimSuffix "-" -}}
{{- end -}}
{{- end -}}

{{- define "incident-pulse.labels" -}}
helm.sh/chart: {{ printf "%s-%s" .Chart.Name .Chart.Version }}
app.kubernetes.io/managed-by: {{ .Release.Service }}
app.kubernetes.io/part-of: incident-pulse
{{ include "incident-pulse.selectorLabels" . }}
{{- end -}}

{{- define "incident-pulse.selectorLabels" -}}
app.kubernetes.io/name: {{ include "incident-pulse.name" . }}
app.kubernetes.io/instance: {{ .Release.Name }}
{{- end -}}

{{- define "incident-pulse.serviceAccountName" -}}
{{- if .Values.serviceAccount.create -}}
{{- include "incident-pulse.fullname" . -}}
{{- else -}}
{{- default "default" .Values.serviceAccount.name -}}
{{- end -}}
{{- end -}}

{{- define "incident-pulse.dynamodbEndpoint" -}}
{{- if .Values.dynamodbLocal.enabled -}}
{{- printf "http://%s-dynamodb:%v" (include "incident-pulse.fullname" .) .Values.dynamodbLocal.port -}}
{{- else -}}
{{- .Values.app.dynamodbEndpoint -}}
{{- end -}}
{{- end -}}
