#!/bin/bash

# Script monitoring untuk BPF Asset System

while true; do
    clear
    echo "=== BPF Asset System Monitor ==="
    echo "Time: $(date)"
    echo ""
    
    # Cek status container
    if docker ps | grep -q bpf-ac-system; then
        echo "? Container Status: RUNNING"
        echo ""
        
        # Container stats
        echo "?? Resource Usage:"
        docker stats --no-stream bpf-ac-system --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}\t{{.NetIO}}"
        echo ""
        
        # Database size
        echo "?? Database Size:"
        docker exec bpf-ac-system ls -lh /app/data/bpf_ac_ai_system.db | awk '{print "   " $5}'
        echo ""
        
        # Last 5 log entries
        echo "?? Last 5 log entries:"
        docker logs --tail 5 bpf-ac-system 2>&1 | grep -v "WARNING"
        
    else
        echo "? Container Status: STOPPED"
    fi
    
    echo ""
    echo "Press Ctrl+C to exit monitoring..."
    sleep 5
done